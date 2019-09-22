# coding: utf-8

from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass, field
from contextlib import contextmanager
from bookworm.logger import logger
from .enumerations import EmphSpec, VolumeSpec, RateSpec, PauseSpec


log = logger.getChild(__name__)


@dataclass(frozen=True)
class SpeechStyle:
    """Voice settings for a single utterance."""

    voice: str = None
    """Voice name."""

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


@dataclass(order=True, frozen=True)
class BaseSpeechUtterance(ABC):
    """A blueprint for speaking some content."""

    priority: int = 0

    @abstractmethod
    def add_text(self, text):
        """Append textual content."""

    @abstractmethod
    def add_sentence(self, sentence):
        """Append a sentence."""

    @contextmanager
    @abstractmethod
    def new_paragraph(self):
        """Create a new paragraph."""

    @abstractmethod
    def add_bookmark(self, bookmark):
        """Append application specific data."""

    @abstractmethod
    @contextmanager
    def set_style(self, style):
        """Temperary set the speech style."""

    @abstractmethod
    def add_pause(self, duration):
        """Append silence to the speech stream.
        `duration` is a PauseSpec enumeration member or an int
        representing silence time in milliseconds.
        """

    @abstractmethod
    def add_audio(self, filename):
        """Append a wave audio file to the speech stream."""

    def _is_valid_operand(self, other):
        return isinstance(other, self.__class__)

    @abstractmethod
    def add(self, utterance):
        """Append the content of another utterance to this utterance."""

    def __iadd__(self, other):
        self.add(other)
        return self
