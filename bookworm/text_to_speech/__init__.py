# coding: utf-8

import wx
import bisect
import ujson as json
from queue import PriorityQueue
from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import dataclass
from bookworm import config
from bookworm.resources import sounds
from bookworm.resources import images
from bookworm.speechdriver import DummySpeechEngine
from bookworm.speechdriver.utterance import SpeechUtterance, SpeechStyle
from bookworm.speechdriver.enumerations import (
    EngineEvent,
    SynthState,
    EmphSpec,
    PauseSpec,
)
from bookworm.speechdriver.engines.sapi import SapiSpeechEngine
from bookworm.speechdriver.engines.onecore import OcSpeechEngine
from bookworm.signals import _signals
from bookworm.utils import cached_property, gui_thread_safe
from bookworm.vendor.sentence_splitter import (
    SentenceSplitter,
    SentenceSplitterException,
    supported_languages as splitter_supported_languages,
)
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
)
from bookworm.base_service import BookwormService
from bookworm.logger import logger
from .tts_config import tts_config_spec, TTSConfigManager
from .tts_gui import (
    ReadingPanel,
    SpeechPanel,
    SpeechMenu,
    SPEECH_KEYBOARD_SHORTCUTS,
    StatelessSpeechMenuIds,
    StatefulSpeechMenuIds,
)

log = logger.getChild(__name__)
MAX_TOKENIZED_CHARS = 7500
speech_engine_state_changed = _signals.signal("speech-engine.state-changed")


@dataclass
class TextInfo:
    """Provides basic structural information  about a blob of text
    Most of the properties have their values cached.
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
        for _nope, pos in segments:
            rv.append(pos + self.start_pos)
        return rv

    @property
    def configured_markers(self):
        return self.paragraph_markers


class TextToSpeechService(BookwormService):
    name = "text_to_speech"
    config_spec = tts_config_spec
    has_gui = True
    stateful_menu_ids = StatefulSpeechMenuIds
    __available_engines = (SapiSpeechEngine, OcSpeechEngine)
    speech_engines = [e for e in __available_engines if e.check()]

    def __post_init__(self):
        self.config_manager = TTSConfigManager()
        self.textCtrl = self.view.contentTextCtrl
        self._current_textinfo = None
        self.queue = PriorityQueue()
        self.engine = None
        reader_book_unloaded.connect(self.on_reader_unload, sender=self.reader)
        reader_page_changed.connect(self._change_page_for_tts, sender=self.reader)
        # maintain state upon startup
        self.on_engine_state_changed(state=SynthState.ready)

    def shutdown(self):
        self.close()

    def process_menubar(self, menubar):
        self.menu = SpeechMenu(self, menubar)

    def get_settings_panels(self):
        return [
            # Translators: the label of a page in the settings dialog
            (10, "reading", ReadingPanel, _("Reading")),
            # Translators: the label of a page in the settings dialog
            (15, "speech", SpeechPanel, _("Voice")),
        ]

    def get_contextmenu_items(self):
        return ()

    def get_toolbar_items(self):
        return [
            (52, "rewind", _("Back"), StatefulSpeechMenuIds.rewind),
            (53, "play", _("Play"), StatefulSpeechMenuIds.playToggle),
            (54, "fastforward", _("Forward"), StatefulSpeechMenuIds.fastforward),
            (55, "profile", _("Voice"), StatelessSpeechMenuIds.voiceProfiles),
            (56, "", "", None),
        ]

    def get_keyboard_shourtcuts(self):
        return SPEECH_KEYBOARD_SHORTCUTS

    def on_reader_unload(self, sender):
        self.close()
        self._current_textinfo = None

    def _change_page_for_tts(self, sender, current, prev):
        if not self.is_engine_ready:
            return
        self._current_textinfo = self.content_tokenized(start_pos=0)
        is_speaking = getattr(self, "_requested_play", False)
        if self.engine.state is not SynthState.ready:
            self.engine.stop()
        if is_speaking:
            utterance = SpeechUtterance()
            if config.conf["reading"]["speak_page_number"]:
                utterance.add_text(
                    # Translators: a message to announce when navigating to another page
                    _("Page {page} of {total}").format(
                        page=self.reader.current_page + 1,
                        total=len(self.reader.document),
                    )
                )
                utterance.add_pause(PauseSpec.medium)
            self.speak_current_page(utterance)

    def make_text_info(self, *args, **kwargs):
        """Add the language of the current document."""
        kwargs.setdefault("lang", self.reader.document.language)
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
        current_pos = start_pos
        if start_pos is None:
            if not config.conf["reading"]["start_reading_from_"]:
                current_pos = self.textCtrl.GetInsertionPoint()
            else:
                current_pos = 0
        text_length = self.textCtrl.GetLastPosition()
        end_of_page = (
            text_length if text_length <= MAX_TOKENIZED_CHARS else MAX_TOKENIZED_CHARS
        )
        text = self.textCtrl.GetRange(current_pos, end_of_page)
        return self.make_text_info(text, start_pos=current_pos)

    def speak_current_page(self, utterance=None, from_caret=True):
        start_pos = self.textCtrl.InsertionPoint if from_caret else 0
        textinfo = self.content_tokenized(start_pos=start_pos)
        if self._current_textinfo is None:
            self._current_textinfo = textinfo
        utterance = utterance or SpeechUtterance()
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
                utterance.add_pause(self.config_manager["paragraph_pause"])
        if config.conf["reading"]["reading_mode"] < 2:
            utterance.add_pause(self.config_manager["end_of_page_pause"])
            page_bookmark = {"type": "end_page", "current": self.reader.current_page}
            utterance.add_bookmark(self.encode_bookmark(page_bookmark))
            utterance.add_text(",\f")
        self.enqueue(utterance)
        self.process_queue()

    @gui_thread_safe
    def process_bookmark(self, bookmark):
        data = self.decode_bookmark(bookmark)
        if data["type"] == "start_segment":
            pos = data["pos"]
            self.textCtrl.ShowPosition(pos)
            if self.textCtrl.GetInsertionPoint() != pos:
                self.textCtrl.SetInsertionPoint(pos)
            if config.conf["reading"]["highlight_spoken_text"]:
                self.view.clear_highlight(0, pos)
                self.view.highlight_range(
                    pos, data["end"], foreground=wx.BLACK, background=wx.LIGHT_GREY
                )
            if config.conf["reading"]["select_spoken_text"]:
                self.textCtrl.SetSelection(pos, data["end"])
        elif data["type"] == "end_page":
            has_next_page = self.reader.navigate(to="next", unit="page")
            if not has_next_page:
                utterance = SpeechUtterance(priority=1)
                if config.conf["reading"]["play_end_of_section_sound"]:
                    utterance.add_audio(sounds.section_changed.path)
                # Translators: a message to speak at the end of the chapter
                utterance.add_text(
                    _("End of section: {chapter}.").format(
                        chapter=self.reader.active_section.title
                    )
                )
                utterance.add_pause(self.config_manager["end_of_section_pause"])
                if config.conf["reading"]["reading_mode"] == 0:
                    nextsect_bookmark = {"type": "next_section"}
                    utterance.add_bookmark(self.encode_bookmark(nextsect_bookmark))
                self.enqueue(utterance)
                self.process_queue()
        elif data["type"] == "next_section":
            self.reader.navigate(to="next", unit="section")

    def fastforward(self):
        if not self._current_textinfo or (self.engine.state is not SynthState.busy):
            return wx.Bell()
        markers = self._current_textinfo.configured_markers
        caret_pos = self.textCtrl.InsertionPoint
        pos = markers[-1]
        index = bisect.bisect_right(markers, caret_pos)
        if index != len(markers):
            pos = markers[index]
        self.textCtrl.SetInsertionPoint(pos)
        self.engine.stop()
        self.speak_current_page(from_caret=True)

    def rewind(self):
        if not self._current_textinfo or (self.engine.state is not SynthState.busy):
            return wx.Bell()
        markers = self._current_textinfo.configured_markers
        caret_pos = self.textCtrl.InsertionPoint
        index = bisect.bisect_left(markers, caret_pos)
        if index:
            index -= 1
        pos = markers[index]
        self.textCtrl.SetInsertionPoint(pos)
        self.engine.stop()
        self.speak_current_page(from_caret=True)

    def initialize_engine(self):
        engine_name = self.config_manager["engine"]
        last_known_state = (
            SynthState.ready if not self.is_engine_ready else self.engine.state
        )
        if self.is_engine_ready and (self.engine.name == engine_name):
            self.configure_engine(last_known_state)
            return
        self.close()
        Engine = self.get_engine(engine_name)
        self.engine = Engine()
        # Event handlers
        self.engine.bind(EngineEvent.state_changed, self.on_state_changed)
        self.engine.bind(EngineEvent.bookmark_reached, self.on_bookmark_reached)
        self.configure_engine(last_known_state)
        self._try_set_tts_language()

    def configure_engine(self, last_known_state=SynthState.ready):
        if not self.is_engine_ready:
            return
        if self.engine.state is not SynthState.ready:
            self.engine.stop()
        try:
            self.engine.configure(self.config_manager)
        except ValueError:
            self.config_manager.restore_defaults()
            self.config_manager.save()
            if self.engine.get_first_available_voice() is None:
                self.reader.view.notify_user(
                    # Translators: the title of a message telling the user that no TTS voice found
                    _("No TTS Voices"),
                    # Translators: a message telling the user that no TTS voice found
                    _(
                        "A valid Text-to-speech voice was not found for the current speech engine.\n"
                        "Text-to-speech functionality will be disabled."
                    ),
                )
        if self.reader.ready and last_known_state is SynthState.busy:
            self.speak_current_page()

    def _try_set_tts_language(self):
        lang = self.reader.document.language
        if (self.engine.voice is not None) and (
            not self.engine.voice.speaks_language(lang)
        ):
            voice_for_lang = self.engine.get_voices_by_language(lang)
            if voice_for_lang:
                self.engine.voice = voice_for_lang[0]
                self.view.notify_user(
                    # Translators: the title of a message telling the user that the TTS voice has been changed
                    _("Incompatible TTS Voice Detected"),
                    # Translators: a message telling the user that the TTS voice has been changed
                    _(
                        "Bookworm has noticed that the currently configured Text-to-speech voice "
                        "speaks a language different from that of this book. "
                        "Because of this, Bookworm has temporary switched to "
                        "another voice that speaks a language similar to the language  of this book."
                    ),
                )

    def close(self):
        if self.engine:
            self.engine.close()
            self.engine = None

    def enqueue(self, utterance):
        if not self.is_engine_ready:
            raise RuntimeError("Not initialized.")
        self.queue.put_nowait(utterance)

    def process_queue(self):
        if not self.is_engine_ready:
            raise RuntimeError("Not initialized.")
        while not self.queue.empty():
            utterance = self.queue.get_nowait()
            self.engine.speak(utterance)

    @property
    def is_engine_ready(self):
        return self.engine is not None

    def on_state_changed(self, sender, state):
        speech_engine_state_changed.send(self.view, service=self, state=state)
        self.on_engine_state_changed(state)

    def on_bookmark_reached(self, sender, bookmark):
        self.process_bookmark(bookmark)

    @gui_thread_safe
    def on_engine_state_changed(self, state):
        if state is SynthState.ready:
            self.view.clear_highlight()
        if state is SynthState.busy:
            image = images.pause
        else:
            image = images.play
        self.view.toolbar.SetToolNormalBitmap(
            StatefulSpeechMenuIds.playToggle, image.GetBitmap()
        )
        if not self.reader.ready:
            return
        menubar = self.view.menuBar
        play = menubar.FindItemById(StatefulSpeechMenuIds.play)
        pause_toggle = menubar.FindItemById(StatefulSpeechMenuIds.pauseToggle)
        fastforward = menubar.FindItemById(StatefulSpeechMenuIds.fastforward)
        rewind = menubar.FindItemById(StatefulSpeechMenuIds.rewind)
        stop = menubar.FindItemById(StatefulSpeechMenuIds.stop)
        pause_toggle.Enable(state is not SynthState.ready)
        stop.Enable(state is not SynthState.ready)
        play.Enable(state is not SynthState.busy)
        fastforward.Enable(state is not SynthState.ready)
        rewind.Enable(state is not SynthState.ready)

    @classmethod
    def get_engine(cls, engine_name):
        engine = DummySpeechEngine
        for e in cls.speech_engines:
            if e.name == engine_name:
                engine = e
                break
        return engine
