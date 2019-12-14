# coding: utf-8

import System
from System.Speech.Synthesis import PromptBuilder, PromptStyle
from contextlib import contextmanager
from pathlib import Path
from bookworm.speech.enumerations import SpeechElementKind, PauseSpec
from bookworm.logger import logger

log = logger.getChild(__name__)


class SapiSpeechUtterance:
    def __init__(self):
        self.prompt = PromptBuilder()

    def populate_from_speech_utterance(self, utterance):
        for element in utterance.speech_sequence:
            self.process_speech_element(element.kind, element.content)

    def process_speech_element(self, elm_kind, content):
        if elm_kind is SpeechElementKind.text:
            self.add_text(content)
        elif elm_kind is SpeechElementKind.sentence:
            self.add_sentence(content)
        elif elm_kind is SpeechElementKind.bookmark:
            self.add_bookmark(content)
        elif elm_kind is SpeechElementKind.pause:
            self.add_pause(content)
        elif elm_kind is SpeechElementKind.audio:
            self.add_audio(content)
        elif elm_kind is SpeechElementKind.start_paragraph:
            self.start_paragraph()
        elif elm_kind is SpeechElementKind.end_paragraph:
            self.end_paragraph()
        elif elm_kind is SpeechElementKind.start_style:
            self.start_style(content)
        elif elm_kind is SpeechElementKind.end_style:
            self.end_style(content)
        else:
            raise TypeError(f"Invalid speech element {element}")

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
        self.start_style(style)
        try:
            yield
        finally:
            self.end_style(style)

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

    def append_utterance(self, utterance):
        """Append the content of another utterance to this utterance."""
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

    def start_paragraph(self):
        self.prompt.StartParagraph()

    def end_paragraph(self):
        self.prompt.EndParagraph()

    def start_style(self, style):
        if style.voice is not None:
            self.prompt.StartVoice(style.voice.name)
        self.prompt.StartStyle(self.prompt_style_from_style(style))

    def end_style(self, style):
        self.prompt.EndStyle()
        if style.voice is not None:
            self.prompt.EndVoice()
