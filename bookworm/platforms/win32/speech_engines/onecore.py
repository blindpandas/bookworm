# coding: utf-8

import platform
import weakref
from pathlib import Path
from weakref import ref

import more_itertools
import neosynth

from bookworm import app
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from bookworm.speechdriver.element.converter.ssml import SsmlSpeechConverter
from bookworm.speechdriver.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speechdriver.enumerations import EngineEvent, RateSpec, SynthState
from bookworm.speechdriver.utterance import SpeechStyle, SpeechUtterance

from .utils import create_audio_bookmark_name, process_audio_bookmark

log = logger.getChild(__name__)
NeosynthStateToSynthState = {
    neosynth.SynthState.Ready: SynthState.ready,
    neosynth.SynthState.Paused: SynthState.paused,
    neosynth.SynthState.Busy: SynthState.busy,
}
RATE_MAP = {
    RateSpec.extra_slow: range(0, 20),
    RateSpec.slow: range(20, 40),
    RateSpec.medium: range(40, 60),
    RateSpec.fast: range(60, 80),
    RateSpec.extra_fast: range(80, 100),
}


class NeosynthSsmlSpeechConverter(SsmlSpeechConverter):
    """Onecore synthesizer does not support the audio element."""

    def audio(self, content):
        return self.bookmark(create_audio_bookmark_name(content))


class EventSink:
    def __init__(self, synthref):
        self.synthref = synthref

    def on_state_changed(self, state):
        if (synth := self.synthref()) is None:
            log.warning(
                "Called on_state_changed method on OneCoreSynth while the synthesizer is dead"
            )
            return
        handlers = synth.event_handlers.get(EngineEvent.state_changed, ())
        for handler in handlers:
            handler(self, NeosynthStateToSynthState[state])

    def on_bookmark_reached(self, bookmark):
        if (synth := self.synthref()) is None:
            log.warning(
                "Called on_state_changed method on OneCoreSynth while the synthesizer is dead"
            )
            return
        if not process_audio_bookmark(bookmark):
            for handler in synth.event_handlers.get(EngineEvent.bookmark_reached, ()):
                handler(self, bookmark)

    def log(self, message, level):
        log.log(level, message)


class OcSpeechEngine(BaseSpeechEngine):
    name = "onecore"
    display_name = _("One-core Synthesizer")
    default_rate = 20
    speech_converter = NeosynthSsmlSpeechConverter()

    def __init__(self):
        super().__init__()
        self.event_sink = EventSink(weakref.ref(self))
        self.synth = neosynth.Neosynth(self.event_sink)
        self.event_handlers = {}
        self.__rate = RateSpec.medium
        self.__pitch = 50

    @classmethod
    def check(self):
        return platform.version().startswith("10")

    def close(self):
        super().close()
        self.event_handlers.clear()
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

    @property
    def pitch(self):
        return int(self.synth.get_pitch())

    @pitch.setter
    def pitch(self, value):
        self.synth.set_pitch(value)

    @property
    def rate(self):
        try:
            return self.synth.get_rate()
        except RuntimeError:
            rate_range = RATE_MAP[self.__rate]
            return round((rate_range.start + rate_range.stop) / 2)

    @rate.setter
    def rate(self, value):
        if 0 <= value <= 100:
            if self.synth.is_prosody_supported():
                self.synth.set_rate(value)
            else:
                self.__rate = more_itertools.first(
                    (k for (k, v) in RATE_MAP.items() if value in v),
                    default=RateSpec.medium,
                )
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

    def preprocess_utterance(self, utterance):
        if not self.synth.is_prosody_supported():
            style_ut = SpeechUtterance()
            with style_ut.set_style(SpeechStyle(rate=self.rate)):
                style_ut.add(utterance)
            utterance = style_ut
        neout = neosynth.SpeechUtterance()
        neout.add_ssml(self.speech_converter.convert(utterance))
        return neout

    def speak_utterance(self, utterance):
        self.synth.speak(utterance)

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
