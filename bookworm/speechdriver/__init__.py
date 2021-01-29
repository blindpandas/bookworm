# coding: utf-8


from bookworm.signals import _signals

speech_engine_state_changed = _signals.signal("speech-engine.state-changed")

from .engine import BaseSpeechEngine
from .enumerations import EngineEvent, SynthState


class DummySpeechEngine(BaseSpeechEngine):
    """A singleton that is used when there are no speech engines."""

    name = "dummy"
    display_name = _("No Speech")

    @classmethod
    def __init_subclass__(cls):
        raise TypeError(f"type 'DummySpeechEngine' is not an acceptable base type")

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
        return 50

    @rate.setter
    def rate(self, value):
        pass

    @property
    def volume(self):
        return 100

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
