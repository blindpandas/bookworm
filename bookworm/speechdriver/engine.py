# coding: utf-8

from abc import ABCMeta, abstractmethod
from dataclasses import field, dataclass
from contextlib import suppress
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from .utterance import SpeechUtterance


log = logger.getChild(__name__)


@dataclass(order=True)
class VoiceInfo:
    id: str = field(compare=False)
    name: str = field(compare=False)
    desc: str = field(compare=False)
    language: LocaleInfo = field(compare=False)
    sort_key: int = 0
    gender: int = field(default=None, compare=False)
    age: int = field(default=None, compare=False)
    data: dict = field(default_factory=dict, compare=False)

    @property
    def display_name(self):
        return self.desc or self.name

    def speaks_language(self, language: LocaleInfo, strict=False):
        return self.language.should_be_considered_equal_to(language, strict=strict)


class BaseSpeechEngine(metaclass=ABCMeta):
    """The base class for speech engines."""

    name = None
    """The name of this speech engine."""
    display_name = None
    default_rate = 50
    default_volume = 75

    def __init__(self):
        if not self.check():
            raise RuntimeError(f"Could not load {self.name} speech engine.")

    @classmethod
    @abstractmethod
    def check(self):
        """Return a bool to indicate whether this engine should be made available."""

    @abstractmethod
    def close(self):
        """Performe any necessary cleanups."""

    def __del__(self):
        with suppress(Exception):
            self.close()

    def configure(self, engine_config):
        if engine_config["voice"]:
            try:
                self.set_voice_from_string(engine_config["voice"])
            except ValueError:
                self.voice = self.get_first_available_voice()
        try:
            if engine_config["rate"] != -1:
                self.rate = engine_config["rate"]
            else:
                self.rate = self.default_rate
        except ValueError:
            self.rate = self.default_rate
        try:
            if engine_config["volume"] != -1:
                self.volume = engine_config["volume"]
            else:
                self.volume = self.default_volume
        except ValueError:
            self.volume = self.default_volume

    @abstractmethod
    def get_voices(self):
        """Return a list of VoiceInfo objects."""

    def get_voices_by_language(self, language: LocaleInfo):
        return sorted(
            voice for voice in self.get_voices() if voice.speaks_language(language)
        )

    @property
    @abstractmethod
    def state(self):
        """Return one of the members of synth state enumeration."""

    @property
    @abstractmethod
    def voice(self):
        """Return the currently configured voice."""

    @voice.setter
    @abstractmethod
    def voice(self, value):
        """Set the current voice."""

    @property
    @abstractmethod
    def rate(self):
        """Get the current speech rate."""

    @rate.setter
    @abstractmethod
    def rate(self, value):
        """Set the speech rate."""

    @property
    @abstractmethod
    def volume(self):
        """Get the current volume level."""

    @volume.setter
    @abstractmethod
    def volume(self, value):
        """Set the current volume level."""

    def speak(self, utterance):
        """Asynchronously speak the given text."""
        if not isinstance(utterance, SpeechUtterance):
            raise TypeError(f"Invalid utterance {utterance}")
        processed_utterance = self.preprocess_utterance(utterance)
        self.speak_utterance(processed_utterance)

    @abstractmethod
    def speak_utterance(self, utterance):
        """Do the actual speech output."""

    @abstractmethod
    def stop(self):
        """Stop the speech."""

    @abstractmethod
    def pause(self):
        """Pause the speech."""

    @abstractmethod
    def resume(self):
        """Resume the speech."""

    @abstractmethod
    def bind(self, event, handler):
        """Bind a member of `EngineEvents` enum to a handler."""

    def set_voice_from_string(self, voice_ident):
        for voice in self.get_voices():
            if voice.id == voice_ident:
                self.voice = voice
                return
        raise ValueError(f"Invalid voice {voice_ident}")

    @classmethod
    def get_first_available_voice(cls, language: LocaleInfo = None):
        _test_engine = cls()
        voices = (
            _test_engine.get_voices_by_language(language=language)
            if language is not None
            else _test_engine.get_voices()
        )
        for voice in voices:
            try:
                _test_engine.set_voice_from_string(voice.id)
                return voice
            except ValueError:
                continue

    def preprocess_utterance(self, utterance):
        """Return engine-specific speech utterance (if necessary)."""
        return utterance
