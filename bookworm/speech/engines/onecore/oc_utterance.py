# coding: utf-8

from System.Speech.Synthesis import PromptBuilder
from dataclasses import dataclass, field
from ..sapi.sp_utterance import SapiSpeechUtterance
from bookworm.logger import logger

log = logger.getChild(__name__)

@dataclass
class OcBookmark:
    bookmark: str


@dataclass(order=True, frozen=True)
class OnecoreSpeechUtterance(SapiSpeechUtterance):
    """A blueprint for speaking some content."""

    speech_sequence: list = field(default_factory=list, compare=False)

    def add_bookmark(self, bookmark):
        self.speech_sequence.append(self.prompt.ToXml())
        self.speech_sequence.append(OcBookmark(bookmark))
        self.prompt.ClearContent()

    def add(self, utterance):
        """Append the content of another utterance to this utterance."""
        self.speech_sequence.extend(utterance.speech_sequence)

    def get_speech_sequence(self):
        self.speech_sequence.append(self.prompt.ToXml())
        self.prompt.ClearContent()
        return self.speech_sequence
