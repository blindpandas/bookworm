# coding: utf-8

import platform
from pathlib import Path
from weakref import ref

import neosynth
from bookworm import app
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from bookworm.speechdriver.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speechdriver.enumerations import (EngineEvent, RateSpec,
                                                SynthState)
from .oc_utterance import OcSpeechUtterance


log = logger.getChild(__name__)
NeosynthStateToSynthState = {
    neosynth.SynthState.Ready: SynthState.ready,
    neosynth.SynthState.Paused: SynthState.paused,
    neosynth.SynthState.Busy: SynthState.busy,
}


class EventSink:

    def __init__(self, synth):
        self.synth = synth

    def on_state_changed(self, state):
        handlers = self.synth.event_handlers.get(EngineEvent.state_changed, ())
        for handler in handlers:
            handler(self, NeosynthStateToSynthState[state])

    def on_bookmark_reached(self, bookmark):
        handlers = self.synth.event_handlers.get(EngineEvent.bookmark_reached, ())
        for handler in handlers:
            handler(self, bookmark)



class OcSpeechEngine(BaseSpeechEngine):

    name = "onecore"
    display_name = _("One-core Synthesizer")
    default_rate = 20

    def __init__(self):
        super().__init__()
        self.event_sink = EventSink(self)
        self.synth = neosynth.Neosynth(self.event_sink)
        self.event_handlers = {}
        self.__rate = 50

    @classmethod
    def check(self):
        return platform.version().startswith("10")

    def close(self):
        super().close()
        self.event_handlers.clear()
        self.event_sink.synth = None
        self.event_sink = None

    def get_voices(self):
        rv = []
        for voice in neosynth.Neosynth.get_voices():
            rv.append(
                VoiceInfo(
                    id=voice.id,
                    name=voice.name,
                    desc=voice.name,
                    language=LocaleInfo(voice.language),
                )
            )
        return rv

    @property
    def state(self):
        return NeosynthStateToSynthState[self.synth.get_state()]

    @property
    def voice(self):
        for voice in self.get_voices():
            if voice.id == self.synth.get_voice().id:
                return voice

    @voice.setter
    def voice(self, value):
        self.synth.set_voice_str(value.id)

    def rate_to_spec(self):
        if 0 <= self._rate <= 20:
            return RateSpec.extra_slow
        elif 21 <= self._rate <= 40:
            return RateSpec.slow
        elif 41 <= self._rate <= 60:
            return RateSpec.medium
        elif 61 <= self._rate <= 100:
            return RateSpec.fast

    @property
    def rate(self):
        try:
            return self.synth.get_rate()
        except RuntimeError:
            return self.__rate

    @rate.setter
    def rate(self, value):
        if 0 <= value <= 100:
            if self.synth.is_prosody_supported():
                self.synth.set_rate(value)
            else:
                self.__rate = value
        else:
            raise ValueError("The provided rate is out of range")

    @property
    def volume(self):
        return int(self.synth.get_volume())

    @volume.setter
    def volume(self, value):
        try:
            self.synth.set_volume(float(value))
        except:
            raise ValueError("The provided volume level is out of range")

    def speak_utterance(self, utterance):
        self.synth.speak(utterance)

    def preprocess_utterance(self, utterance):
        oc_utterance = OcSpeechUtterance(ref(self))
        oc_utterance.populate_from_speech_utterance(utterance)
        return oc_utterance.to_oc_prompt()

    def stop(self):
        self.synth.stop()

    def pause(self):
        self.synth.pause()

    def resume(self):
        self.synth.resume()

    def bind(self, event, handler):
        if event not in (EngineEvent.bookmark_reached, EngineEvent.state_changed):
            raise NotImplementedError
        self.event_handlers.setdefault(event, []).append(handler)

