# coding: utf-8

from .engine import BaseSpeechEngine
from .engines.sapi import SapiSpeechEngine
from .engines.onecore import OcSpeechEngine
from .enumerations import EngineEvent, SynthState


class DummySpeechEngine(BaseSpeechEngine):
    """A dummy speech engine."""

    name = "dummy"
    display_name = _("No Speech")


    @classmethod
    def check(cls):
        return True

    def close(self):
        pass

    def get_voices(self):
        return ()

    @property
    def state(self):
        return SynthState.ready

    @property
    def voice(self):
        return

    @voice.setter
    def voice(self, value):
            pass

    @property
    def rate(self):
        pass

    @rate.setter
    def rate(self, value):
        pass

    @property
    def volume(self):
        pass

    @volume.setter
    def volume(self, value):
        pass

    def speak_utterance(self, utterance):
        pass

    def stop(self):
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    def bind(self, event, handler):
        pass