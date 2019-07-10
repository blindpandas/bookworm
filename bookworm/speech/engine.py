# coding: utf-8

import clr

clr.AddReference("System.Collections")

import System
from System.Collections.Generic import KeyNotFoundException
from System.Speech import Synthesis
from collections import OrderedDict
from contextlib import suppress
from dataclasses import dataclass
from bookworm.logger import logger
from .enumerations import SynthState
from .utterance import SpeechUtterance


log = logger.getChild(__name__)


@dataclass
class VoiceInfo:
    id: str
    name: str
    desc: str
    lang: int
    gender: int
    age: int


class SpeechEngine(Synthesis.SpeechSynthesizer):
    """Our Pythonic Interface to SAPI speech enginge."""

    def __init__(self):
        super().__init__()
        self.SetOutputToDefaultAudioDevice()

    def close(self):
        with suppress(System.ObjectDisposedException):
            self.stop()
        self.Dispose()
        self.Finalize()

    def __del__(self):
        self.close()

    def get_voices(self):
        rv = []
        for voice in self.GetInstalledVoices():
            info = voice.VoiceInfo
            lang = None
            with suppress(KeyNotFoundException):
                lang = info.AdditionalInfo["Language"]
            rv.append(
                VoiceInfo(
                    id=info.Id,
                    name=info.Name,
                    desc=info.Description,
                    lang=lang,
                    gender=info.Gender,
                    age=info.Age,
                )
            )
        return rv

    @property
    def state(self):
        return SynthState(self.State)

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
    def get_first_available_voice(cls):
        _test_engine = cls()
        for voice in _test_engine.get_voices():
            try:
                _test_engine.voice = voice.name
                return voice.name
            except ValueError:
                continue
