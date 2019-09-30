# coding: utf-8

from typing import Any, List
from enum import IntEnum
from dataclasses import dataclass, field
from contextlib import contextmanager
from bookworm.logger import logger
from .enumerations import SpeechElementKind, EmphSpec, VolumeSpec, RateSpec, PauseSpec


log = logger.getChild(__name__)


@dataclass(frozen=True)
class SpeechStyle:
    """Voice settings for a single utterance."""

    voice: object = None
    """VoiceInfo object."""

    emph: EmphSpec = None
    """Speech emphasis."""

    rate: RateSpec = None
    """Speech rate."""

    volume: VolumeSpec = None
    """Voice volume."""

    def __post_init__(self):
        for varname, vartype in self.__annotations__.items():
            if not issubclass(vartype, IntEnum):
                continue
            varvalue = getattr(self, varname)
            if varvalue is not None and not isinstance(varvalue, vartype):
                raise TypeError(f"{varname} must be of type {vartype}")


@dataclass(frozen=True)
class SpeechElement:
    kind: SpeechElementKind
    content: Any


@dataclass(order=True, frozen=True)
class SpeechUtterance:
    """A blueprint for speaking some content."""

    priority: int = 0
    speech_sequence: List[SpeechElement] = field(default_factory=list, compare=False)

    def add_text(self, text):
        """Append textual content."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.text, text))

    def add_sentence(self, sentence):
        """Append a sentence."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.sentence, sentence))

    @contextmanager
    def new_paragraph(self):
        """Create a new paragraph."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.start_paragraph, None))
        try:
            yield
        finally:
            self.speech_sequence.append(SpeechElement(SpeechElementKind.end_paragraph, None))

    def add_bookmark(self, bookmark):
        """Append application specific data."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.bookmark, bookmark))

    @contextmanager
    def set_style(self, style):
        """Temperary set the speech style."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.start_style, style))
        try:
            yield
        finally:
            self.speech_sequence.append(SpeechElement(SpeechElementKind.end_style, style))

    def add_pause(self, duration):
        """Append silence to the speech stream.
        `duration` is a PauseSpec enumeration member or an int
        representing silence time in milliseconds.
        """
        self.speech_sequence.append(SpeechElement(SpeechElementKind.pause, duration))

    def add_audio(self, filename):
        """Append a wave audio file to the speech stream."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.audio, filename))

    def _is_valid_operand(self, other):
        return isinstance(other, self.__class__)

    def add(self, utterance):
        """Append the content of another utterance to this utterance."""
        if not _is_valid_operand(utterance):
            raise TypeError(f"Could not join utterance of type '{type(utterance)}' to utterance of type '{type(self)}'")
        self.speech_sequence.extend(utterance.speech_sequence)

    def __iadd__(self, other):
        self.add(other)
        return self
