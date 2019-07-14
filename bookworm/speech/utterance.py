# coding: utf-8

import System
from System.Speech.Synthesis import PromptBuilder, PromptStyle
from enum import IntEnum
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
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

    @property
    def prompt_style(self):
        """Creates the actual PromptStyle and return it."""
        style = PromptStyle()
        if self.rate is not None:
            style.Rate = self.rate
        if self.volume is not None:
            style.Volume = self.volume
        if self.emph is not None:
            style.Emphasis = self.emph
        return style


@dataclass(order=True, frozen=True)
class SpeechUtterance:
    """A blueprint for speaking some content."""

    priority: int = 0
    prompt: PromptBuilder = field(
        default_factory=lambda: PromptBuilder(), compare=False
    )

    def add_text(self, text):
        """Append textual content."""
        self.prompt.AppendText(text)

    def add_sentence(self, sentence):
        """Append a sentence."""
        self.prompt.StartSentence()
        self.add_text(sentence)
        self.prompt.EndSentence()

    @contextmanager
    def new_paragraph(self):
        """Create a new paragraph."""
        self.prompt.StartParagraph()
        try:
            yield
        finally:
            self.prompt.EndParagraph()

    def add_bookmark(self, bookmark):
        """Append application specific data."""
        self.prompt.AppendBookmark(bookmark)

    @contextmanager
    def set_style(self, style):
        """Temperary set the speech style."""
        _has_voice = style.voice is not None
        if _has_voice:
            self.prompt.StartVoice(style.voice)
        self.prompt.StartStyle(style.prompt_style)
        try:
            yield
        finally:
            self.prompt.EndStyle()
            if _has_voice:
                self.prompt.EndVoice()

    def add_pause(self, duration):
        """Append silence to the speech stream.
        `duration` is a PauseSpec enumeration member or an int
        representing silence time in milliseconds.
        """
        if isinstance(duration, PauseSpec):
            pause = int(duration)
        else:
            pause = System.TimeSpan.FromMilliseconds(duration)
        self.prompt.AppendBreak(pause)

    def add_audio(self, filename):
        """Append a wave audio file to the speech stream."""
        uri = Path(filename).as_uri()
        self.prompt.AppendAudio(uri)

    def _is_valid_operand(self, other):
        return isinstance(other, self.__class__)

    def add(self, utterance):
        """Append the content of another utterance to this utterance."""
        if not self._is_valid_operand(utterance):
            raise TypeError(
                'can only add SpeechUtterance (not "{type(utterance)}") to SpeechUtterance'
            )
        self.prompt.AppendPromptBuilder(utterance.prompt)

    def __str__(self):
        return self.prompt.ToXml()

    def __bool__(self):
        return not self.prompt.IsEmpty

    def __eq__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.prompt.Equals(other)

    def __iadd__(self, other):
        self.add(other)
        return self
