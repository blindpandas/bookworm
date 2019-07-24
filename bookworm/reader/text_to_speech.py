# coding: utf-8

import wx
import bisect
import ujson as json
from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import dataclass
from bookworm import config
from bookworm import sounds
from bookworm.speech import SpeechProvider
from bookworm.speech.utterance import SpeechUtterance, SpeechStyle
from bookworm.speech.enumerations import SynthState, EmphSpec, PauseSpec
from bookworm.utils import cached_property, gui_thread_safe
from bookworm.sentence_splitter import (
    SentenceSplitter,
    SentenceSplitterException,
    supported_languages as splitter_supported_languages,
)
from bookworm.signals import (
    reader_book_unloaded,
    reader_page_changed,
    speech_engine_state_changed,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


@dataclass
class TextInfo:
    """Provides basic structural information  about a blob of text
    This class is optimized for repeated calls.
    """

    text: str
    """The text blob to process."""

    start_pos: int = 0
    """Starting position of the text, i.e. in a text control or a stream."""

    lang: str = "en"
    """The natural language of the text. Used in splitting the text into sentences."""

    eol: str = None
    """The recognizable end-of-line sequence. Used to split the text into paragraphs."""

    def __post_init__(self):
        lang = self.lang
        if lang not in splitter_supported_languages():
            lang = "en"
        self._sent_tokenizer = SentenceSplitter(lang)

    @cached_property
    def sentence_markers(self):
        return self._record_markers(self.sentences)

    @cached_property
    def paragraph_markers(self):
        return self._record_markers(self.paragraphs)

    def split_sentences(self, textblock):
        return self._sent_tokenizer.split(textblock)

    @cached_property
    def sentences(self):
        rv = []
        for sent in self.split_sentences(self.text):
            if sent.strip():
                # XXX FixME: Find a way to get the starting position of this sentence
                pos = self.text.find(sent)
                rv.append((sent, pos + self.start_pos))
        return rv

    @cached_property
    def paragraphs(self):
        rv = []
        if self.eol is None:
            paragraphs = self.text.splitlines()
        else:
            paragraphs = self.text.split(self.eol)
        for parag in paragraphs:
            if parag.strip():
                pos = self.text.index(parag)
                rv.append((parag, pos + self.start_pos))
        return rv

    def _record_markers(self, segments):
        rv = []
        for _, pos in segments:
            rv.append(pos + self.start_pos)
        return rv

    @property
    def configured_markers(self):
        return self.paragraph_markers


class TextToSpeechProvider:
    """A mixin to add text-to-speech functionality to the reader."""

    def __init__(self):
        self.tts = SpeechProvider(self)
        self._current_textinfo = None
        reader_book_unloaded.connect(self._tts_on_unload, sender=self)
        reader_page_changed.connect(self._change_page_for_tts, sender=self)
        speech_engine_state_changed.connect(self._on_tts_state_changed, sender=self.tts)

    def _tts_on_unload(self, sender):
        self.tts.close()
        self._current_textinfo = None

    def _change_page_for_tts(self, sender, current, prev):
        if not self.tts.is_ready:
            return
        self._current_textinfo = self.content_tokenized(start_pos=0)
        is_speaking = getattr(self.tts, "_requested_play", False)
        if self.tts.engine.state is not SynthState.ready:
            self.tts.engine.stop()
        if is_speaking:
            utterance = SpeechUtterance()
            if config.conf["reading"]["speak_page_number"]:
                utterance.add_text(
                    f"Page {self.current_page + 1} of {len(self.document)}"
                )
                utterance.add_pause(PauseSpec.medium)
            self.speak_current_page(utterance)

    def make_text_info(self, *args, **kwargs):
        """Add the language of the current document."""
        kwargs.setdefault("lang", self.document.language)
        return TextInfo(*args, **kwargs)

    def encode_bookmark(self, data):
        dump = json.dumps(data, encode_html_chars=True, ensure_ascii=True).encode(
            "ascii"
        )
        return urlsafe_b64encode(dump).decode("ascii")

    def decode_bookmark(self, string):
        data = urlsafe_b64decode(string.encode("ascii"))
        return json.loads(data)

    def content_tokenized(self, start_pos=None):
        textCtrl = self.view.contentTextCtrl
        current_pos = start_pos
        if start_pos is None:
            if not config.conf["reading"]["start_reading_from_"]:
                current_pos = textCtrl.GetInsertionPoint()
            else:
                current_pos = 0
        end_of_page = textCtrl.GetLastPosition()
        text = textCtrl.GetRange(current_pos, end_of_page)
        return self.make_text_info(text, start_pos=current_pos)

    def speak_current_page(self, utterance=None):
        if self._current_textinfo is None:
            self._current_textinfo = self.content_tokenized(start_pos=0)
        utterance = utterance or SpeechUtterance()
        textinfo = self.content_tokenized()
        for text, pos in textinfo.paragraphs:
            with utterance.new_paragraph():
                bookmark_data = {
                    "type": "start_segment",
                    "pos": pos,
                    "end": pos + len(text),
                }
                utterance.add_bookmark(self.encode_bookmark(bookmark_data))
                sent_pause = config.conf["speech"]["sentence_pause"]
                for sent in textinfo.split_sentences(text):
                    utterance.add_sentence(sent + " ")
                    if sent_pause:
                        utterance.add_pause(sent_pause)
                utterance.add_pause(config.conf["speech"]["paragraph_pause"])
        if config.conf["reading"]["reading_mode"] < 2:
            utterance.add_pause(config.conf["speech"]["end_of_page_pause"])
            page_bookmark = {"type": "end_page", "current": self.current_page}
            utterance.add_bookmark(self.encode_bookmark(page_bookmark))
            utterance.add_text(".\f")
        self.tts.enqueue(utterance)
        self.tts.process_queue()

    @gui_thread_safe
    def process_bookmark(self, bookmark):
        data = self.decode_bookmark(bookmark)
        if data["type"] == "start_segment":
            textCtrl = self.view.contentTextCtrl
            pos = data["pos"]
            textCtrl.ShowPosition(pos)
            if textCtrl.GetInsertionPoint() != pos:
                textCtrl.SetInsertionPoint(pos)
            if config.conf["reading"]["highlight_spoken_text"]:
                self.view.clear_highlight(0, pos)
                self.view.highlight_text(pos, data["end"])
            if config.conf["reading"]["select_spoken_text"]:
                textCtrl.SetSelection(pos, data["end"])
        elif data["type"] == "end_page":
            has_next_page = self.navigate(to="next", unit="page")
            if not has_next_page:
                utterance = SpeechUtterance(priority=1)
                if config.conf["reading"]["play_end_of_section_sound"]:
                    utterance.add_audio(sounds.section_changed.path)
                with utterance.set_style(SpeechStyle(emph=EmphSpec.strong)):
                    utterance.add_text(f"End of section: {self.active_section.title}.")
                utterance.add_pause(config.conf["speech"]["end_of_section_pause"])
                if config.conf["reading"]["reading_mode"] == 0:
                    nextsect_bookmark = {"type": "next_section"}
                    utterance.add_bookmark(self.encode_bookmark(nextsect_bookmark))
                self.tts.enqueue(utterance)
                self.tts.process_queue()
        elif data["type"] == "next_section":
            self.navigate(to="next", unit="section")

    def fastforward(self):
        if not self._current_textinfo or (self.tts.engine.state is not SynthState.busy):
            return wx.Bell()
        markers = self._current_textinfo.configured_markers
        caret_pos = self.view.contentTextCtrl.InsertionPoint
        pos = markers[-1]
        index = bisect.bisect_right(markers, caret_pos)
        if index != len(markers):
            pos = markers[index]
        self.view.contentTextCtrl.SetInsertionPoint(pos)
        self.tts.engine.stop()
        self.speak_current_page()

    def rewind(self):
        if not self._current_textinfo or (self.tts.engine.state is not SynthState.busy):
            return wx.Bell()
        markers = self._current_textinfo.configured_markers
        caret_pos = self.view.contentTextCtrl.InsertionPoint
        index = bisect.bisect_left(markers, caret_pos)
        if index:
            index -= 1
        pos = markers[index]
        self.view.contentTextCtrl.SetInsertionPoint(pos)
        self.tts.engine.stop()
        self.speak_current_page()

    def _on_tts_state_changed(self, sender, state):
        if state is SynthState.ready:
            self.view.clear_highlight()
