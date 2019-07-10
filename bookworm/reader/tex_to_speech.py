# coding: utf-8

import wx
import bisect
import json
from bookworm import config
from bookworm import sounds
from bookworm.speech import SpeechProvider
from bookworm.speech.utterance import SpeechUtterance, SpeechStyle
from bookworm.speech.enumerations import SynthState, EmphSpec, PauseSpec
from bookworm.utils import gui_thread_safe
from bookworm.signals import (
    reader_book_unloaded,
    reader_page_changed,
    speech_engine_state_changed,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


class TextToSpeechProvider:
    """A mixin to add text-to-speech functionality to the reader."""

    def __init__(self):
        self.tts = SpeechProvider(self)
        self._paragraph_markers = []
        reader_book_unloaded.connect(
            lambda s: self.tts.close(), sender=self, weak=False
        )
        reader_page_changed.connect(self.change_page_for_tts, sender=self)
        speech_engine_state_changed.connect(self._on_tts_state_changed, sender=self.tts)

    def change_page_for_tts(self, sender, current, prev):
        self._record_paragraph_markers()
        if not self.tts.is_ready:
            return
        is_speaking = self.tts.engine.state is SynthState.busy
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

    def content_tokenized(self, page_number, start_pos=None):
        # XXX More refactoring is needed
        textCtrl = self.view.contentTextCtrl
        current_pos = start_pos
        if start_pos is None:
            if not config.conf["reading"]["start_reading_from_"]:
                current_pos = textCtrl.GetInsertionPoint()
            else:
                current_pos = 0
        end_of_page = textCtrl.GetLastPosition()
        text = textCtrl.GetRange(current_pos, end_of_page)
        if not text:
            return
        parags = text.split("\n")
        for parag in parags:
            if not parag.strip():
                continue
            pos = current_pos + text.index(parag)
            yield (parag, pos)

    def speak_current_page(self, utterance=None):
        utterance = utterance or SpeechUtterance()
        for text, pos in self.content_tokenized(self.current_page):
            bookmark_data = json.dumps(
                {"type": "start_paragraph", "pos": pos, "end": pos + len(text)}
            )
            utterance.add_bookmark(bookmark_data)
            sent_pause = config.conf["speech"]["sentence_pause"]
            if not sent_pause:
                utterance.add_text(text)
            else:
                # XXX Is it worth the overhead of using a NLP based approach
                # Perhaps there is an even better option
                for sent in text.split("."):
                    if not sent:
                        continue
                    utterance.add_text(sent)
                    utterance.add_pause(sent_pause)
            utterance.add_pause(config.conf["speech"]["paragraph_pause"])
        if config.conf["reading"]["reading_mode"] < 2:
            utterance.add_pause(config.conf["speech"]["end_of_page_pause"])
            utterance.add_text(".\f")
            page_bookmark = json.dumps(
                {"type": "end_page", "current": self.current_page}
            )
            utterance.add_bookmark(page_bookmark)
        self.tts.enqueue(utterance)
        self.tts.process_queue()

    @gui_thread_safe
    def process_bookmark(self, bookmark):
        data = json.loads(bookmark)
        if data["type"] == "start_paragraph":
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
                with utterance.set_style(SpeechStyle(emph=EmphSpec.moderate)):
                    utterance.add_text(f"End of section: {self.active_section.title}.")
                utterance.add_pause(config.conf["speech"]["end_of_section_pause"])
                if config.conf["reading"]["reading_mode"] == 0:
                    nextsect_bookmark = json.dumps({"type": "next_section"})
                    utterance.add_bookmark(nextsect_bookmark)
                self.tts.enqueue(utterance)
                self.tts.process_queue()
        elif data["type"] == "next_section":
            self.navigate(to="next", unit="section")

    def _record_paragraph_markers(self):
        self._paragraph_markers.clear()
        for _, pos in self.content_tokenized(self.current_page, start_pos=0):
            self._paragraph_markers.append(pos)

    def fastforward(self):
        if not self._paragraph_markers or (
            self.tts.engine.state is not SynthState.busy
        ):
            return wx.Bell()
        caret_pos = self.view.contentTextCtrl.InsertionPoint
        pos = self._paragraph_markers[-1]
        index = bisect.bisect_right(self._paragraph_markers, caret_pos)
        if index != len(self._paragraph_markers):
            pos = self._paragraph_markers[index]
        self.view.contentTextCtrl.SetInsertionPoint(pos)
        self.tts.engine.stop()
        self.speak_current_page()

    def rewind(self):
        if not self._paragraph_markers or (
            self.tts.engine.state is not SynthState.busy
        ):
            return wx.Bell()
        caret_pos = self.view.contentTextCtrl.InsertionPoint
        index = bisect.bisect_left(self._paragraph_markers, caret_pos)
        if index:
            index -= 1
        pos = self._paragraph_markers[index]
        self.view.contentTextCtrl.SetInsertionPoint(pos)
        self.tts.engine.stop()
        self.speak_current_page()

    def alert_for_tts_error(self, message):
        wx.MessageBox(message, "No voices", wx.ICON_ERROR)

    def _on_tts_state_changed(self, sender, state):
        if state is SynthState.ready:
            self.view.clear_highlight()
