# coding: utf-8

from abc import ABCMeta, abstractmethod
from dataclasses import field, dataclass
from bookworm.logger import logger


log = logger.getChild(__name__)


@dataclass
class VoiceInfo:
    id: str
    name: str
    desc: str
    language: str
    gender: int = None
    age: int = None
    data: dict = field(default_factory=dict)

    @property
    def display_name(self):
        return self.desc or self.name

    def speaks_language(self, language):
        return self.language.startswith(language.lower())


class BaseSpeechEngine(metaclass=ABCMeta):
    """The base class for speech engines."""

    name = None
    """The name of this speech engine."""
    display_name = None
    """The user-friendly, localizable name of this engine."""
    utterance_cls = None

    def __init__(self, language=None):
        self._language = language

    @classmethod
    @abstractmethod
    def check(self):
        """Return a bool to indicate whether this engine should be made available."""

    @abstractmethod
    def close(self):
        """Performe any necessary cleanups."""

    def __del__(self):
        self.close()

    @abstractmethod
    def get_voices(self, language=None):
        """Return a list of VoiceInfo objects."""

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

    @abstractmethod
    def speak(self, utterance):
        """Asynchronously speak the given text."""
        if not isinstance(utterance, self.utterance_cls):
            raise TypeError(f"Invalid utterance {utterance}")

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

    @classmethod
    def get_first_available_voice(cls, language=None):
        _test_engine = cls()
        for voice in _test_engine.get_voices(language=language):
            try:
                _test_engine.set_voice_from_string(voice.id)
                return voice.id
            except ValueError:
                continue

    @classmethod
    def make_utterance(cls, *args, **kwargs):
        """Return a new utterance object that is compatable with this speech engine."""
        return cls.utterance_cls(*args, **kwargs)

