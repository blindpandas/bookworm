# coding: utf-8


import uuid
from copy import deepcopy
from pathlib import Path
from configobj import ConfigObj, ConfigObjError, ParseError
from validate import Validator, ValidateError
from bookworm.paths import config_path
from bookworm.concurrency import call_threaded
from bookworm.config.spec import speech_spec, builtin_voice_profiles



import wx
import bisect
import ujson as json
from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import dataclass
from bookworm import sounds
from bookworm.services import BookwormService, ServiceGUIManager
from bookworm.speech import SpeechProvider
from bookworm.speech.utterance import SpeechUtterance, SpeechStyle
from bookworm.speech.enumerations import SynthState, EmphSpec, PauseSpec
from bookworm.utils import cached_property, gui_thread_safe
from bookworm.vendor.sentence_splitter import (
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
from .tts_gui import TTSGUIManager
from .tts_config_manager import SpeechConfigManager


log = logger.getChild(__name__)


@dataclass
class TextInfo:
    """Provides basic structural information  about a blob of text
    Most of the properties are executed once, then their value is cached.
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
    name = "tts"
    gui_manager = TTSGUIManager

    def __post_init__(self):
        self.config = SpeechConfigManager(self)
        self.tts = SpeechProvider(self.reader)
        self._current_textinfo = None

    def setup_event_handlers(self):
        reader_book_unloaded.connect(self._tts_on_unload, sender=self)
        reader_page_changed.connect(self._change_page_for_tts, sender=self)
        speech_engine_state_changed.connect(self._on_tts_state_changed, sender=self.tts)

    @classmethod
    def setup_config(self, spec):
        return "speech", speech_spec


