# coding: utf-8

import System
from System.Speech.Synthesis import PromptBuilder, PromptStyle
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from bookworm.speech.enumerations import PauseSpec
from bookworm.speech.utterance import BaseSpeechUtterance
from bookworm.logger import logger

log = logger.getChild(__name__)



@dataclass(order=True, frozen=True)
class SapiSpeechUtterance(BaseSpeechUtterance):
    """A blueprint for speaking some content."""

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
            self.prompt.StartVoice(style.voice.name)
        self.prompt.StartStyle(self.prompt_style_from_style(style))
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

    def add(self, utterance):
        """Append the content of another utterance to this utterance."""
        if not self._is_valid_operand(utterance):
            raise TypeError(
                'can only add SpeechUtterance (not "{type(utterance)}") to SpeechUtterance'
            )
        self.prompt.AppendPromptBuilder(utterance.prompt)

    @staticmethod
    def prompt_style_from_style(style):
        """Creates the actual PromptStyle and return it."""
        pstyle = PromptStyle()
        if style.rate is not None:
            pstyle.Rate = style.rate
        if style.volume is not None:
            pstyle.Volume = style.volume
        if style.emph is not None:
            pstyle.Emphasis = style.emph
        return pstyle
