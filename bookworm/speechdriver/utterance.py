# coding: utf-8

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import get_type_hints

from bookworm import typehints as t
from bookworm.logger import logger

from .element import SpeechElement, SpeechStyle
from .element.enums import (EmphSpec, PauseSpec, RateSpec, SpeechElementKind,
                            VolumeSpec)

log = logger.getChild(__name__)


@dataclass(order=True, frozen=True)
class SpeechUtterance:
    """A blueprint for speaking some content."""

    priority: int = 0
    speech_sequence: list[SpeechElement] = field(default_factory=list, compare=False)

    def add_text(self, text):
        """Append textual content."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.text, text))

    def add_sentence(self, sentence):
        """Append a sentence."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.sentence, sentence))

    @contextmanager
    def new_paragraph(self):
        """Create a new paragraph."""
        self.speech_sequence.append(
            SpeechElement(SpeechElementKind.start_paragraph, None)
        )
        try:
            yield
        finally:
            self.speech_sequence.append(
                SpeechElement(SpeechElementKind.end_paragraph, None)
            )

    def add_bookmark(self, bookmark):
        """Append application specific data."""
        self.speech_sequence.append(SpeechElement(SpeechElementKind.bookmark, bookmark))

    @contextmanager
    def set_style(self, style):
        """Temperary set the speech style."""
        self.speech_sequence.extend(style.start_style_decompose())
        try:
            yield
        finally:
            self.speech_sequence.extend(style.end_style_decompose())

    def add_pause(self, duration):
        """Append silence to the speech stream.
        `duration` is a PauseSpec enumeration member or an int
        representing silence time in milliseconds.
        """
        self.speech_sequence.append(SpeechElement(SpeechElementKind.pause, duration))

    def add_audio(self, file_uri_or_path):
        """Append a wave audio file to the speech stream."""
        if "://" not in file_uri_or_path:
            file_uri_or_path = Path(file_uri_or_path).as_uri()
        self.speech_sequence.append(
            SpeechElement(SpeechElementKind.audio, file_uri_or_path)
        )

    def _is_valid_operand(self, other):
        return isinstance(other, self.__class__)

    def add(self, utterance):
        """Append the content of another utterance to this utterance."""
        if not self._is_valid_operand(utterance):
            raise TypeError(
                f"Could not join utterance of type '{type(utterance)}' to utterance of type '{type(self)}'"
            )
        self.speech_sequence.extend(utterance.speech_sequence)

    def __iter__(self):
        return iter(self.speech_sequence)

    def __len__(self):
        return len(self.speech_sequence)

    def __iadd__(self, other):
        self.add(other)
        return self
