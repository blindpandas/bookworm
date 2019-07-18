# coding: utf-8

import System
from System.Globalization import CultureInfo
from System.Speech import Synthesis
from collections import OrderedDict
from contextlib import suppress
from dataclasses import dataclass
from bookworm.resources.lang_locales import locale_map
from bookworm.logger import logger
from .enumerations import SynthState
from .utterance import SpeechUtterance


log = logger.getChild(__name__)


@dataclass
class VoiceInfo:
    id: str
    name: str
    desc: str
    language: str
    gender: int
    age: int

    def speaks_language(self, language):
        return self.language.startswith(language.lower())


class SpeechEngine(Synthesis.SpeechSynthesizer):
    """Our Pythonic Interface to SAPI speech enginge."""

    def __init__(self, language=None):
        super().__init__()
        self._language = language
        self.SetOutputToDefaultAudioDevice()

    def close(self):
        with suppress(System.ObjectDisposedException):
            self.stop()
        self.Dispose()
        self.Finalize()

    def __del__(self):
        self.close()

    def get_voices(self, language=None):
        rv = []
        voices = []
        if language is not None:
            current_culture = CultureInfo.CurrentCulture
            if current_culture.IetfLanguageTag.startswith(language.lower()):
                voices.extend(self.GetInstalledVoices(current_culture))
            if language in locale_map:
                for locale in locale_map[language]:
                    culture = CultureInfo.GetCultureInfoByIetfLanguageTag(
                        f"{language}-{locale}"
                    )
                    voices.extend(self.GetInstalledVoices(culture))
            voices.extend(self.GetInstalledVoices(CultureInfo(language)))
        else:
            voices = self.GetInstalledVoices()
        if not voices:
            log.warning("No suitable TTS voice was found.")
            return rv
        for voice in voices:
            if not voice.Enabled:
                continue
            info = voice.VoiceInfo
            rv.append(
                VoiceInfo(
                    id=info.Id,
                    name=info.Name,
                    desc=info.Description,
                    language=info.Culture.IetfLanguageTag,
                    gender=info.Gender,
                    age=info.Age,
                )
            )
        return rv

    @property
    def state(self):
        return SynthState(self.State)

    def get_current_voice(self):
        for voice in self.get_voices():
            if voice.name == self.voice:
                return voice

    @property
    def voice(self):
        return self.Voice.Name

    @voice.setter
    def voice(self, value):
        try:
            self.SelectVoice(value)
        except System.ArgumentException:
            raise ValueError(f"Can not set voice. {value} is an invalid voice name.")

    @property
    def rate(self):
        return self.Rate

    @rate.setter
    def rate(self, value):
        if not (0 <= value <= 100):
            raise ValueError(f"Value {value} for rate is out of range.")
        self.Rate = (value - 50) / 5

    @property
    def volume(self):
        return self.volume

    @volume.setter
    def volume(self, value):
        if not (0 <= value <= 100):
            raise ValueError(f"Value {value} for volume is out of range.")
        self.Volume = value

    def speak(self, utterance):
        if not isinstance(utterance, SpeechUtterance):
            raise TypeError(f"Invalid utterance {utterance}")
        if self._language is not None:
            utterance.prompt.Culture = CultureInfo.GetCultureInfoByIetfLanguageTag(
                self._language
            )
        self.SpeakAsync(utterance.prompt)

    def stop(self):
        if self.state is not SynthState.ready:
            if self.state is SynthState.paused:
                self.Resume()
            self.SpeakAsyncCancelAll()

    def pause(self):
        if self.state is SynthState.busy:
            self.Pause()

    def resume(self):
        if self.state is SynthState.paused:
            self.Resume()

    @classmethod
    def get_first_available_voice(cls, language=None):
        _test_engine = cls()
        for voice in _test_engine.get_voices(language=language):
            try:
                _test_engine.voice = voice.name
                return voice.name
            except ValueError:
                continue
