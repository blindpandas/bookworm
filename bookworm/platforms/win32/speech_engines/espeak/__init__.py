# coding: utf-8

import os
import weakref
from pathlib import Path

import more_itertools
from bookworm.paths import data_path
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from bookworm.speechdriver.utterance import SpeechUtterance
from bookworm.speechdriver.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speechdriver.enumerations import (SynthState, EngineEvent, SpeechElementKind, RateSpec, VolumeSpec, PauseSpec)
from bookworm.speechdriver.element.converter.ssml import SsmlSpeechConverter
from bookworm.platforms.win32.nvwave import WavePlayer

from ..utils import create_audio_bookmark_name, process_audio_bookmark
from . import _espeak

log = logger.getChild(__name__)


RATE_BOOST_MULTIPLIER = 3
META_BOOKMARK_START = "$MBKW_START"

class ESpeakSsmlSpeechConverter(SsmlSpeechConverter):
    """eSpeak synthesizer does not support the audio element."""

    def audio(self, content):
        return self.bookmark(create_audio_bookmark_name(content))


class EventSink:
    def __init__(self, synthref):
        self.synthref = synthref
        self._state = SynthState.ready

    def on_state_changed(self, state):
        if state is self._state:
            return
        if (synth := self.synthref()) is None:
            log.warning(
                "Called on_state_changed method on OneCoreSynth while the synthesizer is dead"
            )
            self._state = SynthState.ready
            return
        self._state = state
        handlers = synth.event_handlers.get(EngineEvent.state_changed, ())
        for handler in handlers:
            handler(self, state)

    def on_bookmark_reached(self, bookmark):
        if (synth := self.synthref()) is None:
            log.warning(
                "Called on_bookmark_reached method on synth while the synthesizer is dead"
            )
            return
        if process_audio_bookmark(bookmark):
            return
        for handler in synth.event_handlers.get(EngineEvent.bookmark_reached, ()):
            handler(self, bookmark)


class ESpeakSpeechEngine(BaseSpeechEngine):
    name = "espeakng"
    display_name = _("eSpeak NG")
    default_rate = 50
    speech_converter = ESpeakSsmlSpeechConverter()

    def __init__(self):
        super().__init__()
        self.event_sink = EventSink(weakref.ref(self))
        self.event_handlers = {}
        _espeak.initialize(self._espeak_bookmark_callback)
        default_voice = more_itertools.first(
            (v for v in self.get_voices() if v.language.ietf_tag == "en-US"),
            default=self.get_voices()[0]
        )
        _espeak.setVoice(default_voice.data["es_voice"])

    @classmethod
    def check(self):
        return True

    def close(self):
        super().close()
        self.event_handlers.clear()
        self.event_sink = None

    def get_voices(self):
        rv = []
        for v in _espeak.getVoiceList():
            if v.identifier is None:
                continue
            identifier  = os.path.basename(_espeak.decodeEspeakString(v.identifier)).lower().split("+")[0]
            lang =_espeak.decodeEspeakString(v.languages[1:])
            name = _espeak.decodeEspeakString(v.name)
            try:
                voice_locale = LocaleInfo(lang)
            except ValueError:
                log.exception("Failed to set voice locale", exc_info=True)
                continue
            rv.append(
                VoiceInfo(
                    id=identifier,
                    name=name,
                    desc=f"{name} ({lang})",
                    language=voice_locale,
                    data={
                        "id": v.identifier,
                        "es_voice": v,
                    }
                )
            )
        return rv

    @property
    def state(self):
        return self.event_sink._state

    @property
    def voice(self):
        es_voice = _espeak.getCurrentVoice()
        current_identifier  = es_voice.identifier
        for voice in self.get_voices():
            if current_identifier == voice.data["id"]:
                return voice

    @voice.setter
    def voice(self, value):
        _espeak.setVoice(value.data["es_voice"])

    @property
    def rate(self):
        val = _espeak.getParameter(_espeak.espeakRATE,1)
        val=int(val/ RATE_BOOST_MULTIPLIER)
        return self.paramToPercent(val,_espeak.minRate,_espeak.maxRate)

    @rate.setter
    def rate(self, value):
        val = self.percentToParam(value, _espeak.minRate, _espeak.maxRate)
        val=int(val* RATE_BOOST_MULTIPLIER)
        _espeak.setParameter(_espeak.espeakRATE,val,0)

    @property
    def pitch(self):
        val=_espeak.getParameter(_espeak.espeakPITCH,1)
        return self.paramToPercent(val,_espeak.minPitch,_espeak.maxPitch)

    @pitch.setter
    def pitch(self, value):
        val=self.percentToParam(value, _espeak.minPitch, _espeak.maxPitch)
        _espeak.setParameter(_espeak.espeakPITCH,val,0)

    @property
    def volume(self):
        return _espeak.getParameter(_espeak.espeakVOLUME,1)

    @volume.setter
    def volume(self, value):
        _espeak.setParameter(_espeak.espeakVOLUME,value,0)

    def preprocess_utterance(self, utterance):
        ut = SpeechUtterance()
        ut.add_bookmark(META_BOOKMARK_START)
        ut.add(utterance)
        return ut

    def speak_utterance(self, utterance):
        ssml = self.speech_converter.convert(utterance)
        _espeak.speak(ssml)

    def stop(self):
        _espeak.stop()
        self.event_sink.on_state_changed(SynthState.ready)

    def pause(self):
        _espeak.pause(True)
        self.event_sink.on_state_changed(SynthState.paused)

    def resume(self):
        _espeak.pause(False)
        self.event_sink.on_state_changed(SynthState.busy)

    def _espeak_bookmark_callback(self, bookmark):
        if bookmark is None:
            self.event_sink.on_state_changed(SynthState.ready)
        elif bookmark == META_BOOKMARK_START:
            self.event_sink.on_state_changed(SynthState.busy)
        else:
            self.event_sink.on_bookmark_reached(bookmark)

    @staticmethod
    def paramToPercent(current: int, min: int, max: int) -> int:
        """Convert a raw parameter value to a percentage given the current, minimum and maximum raw values.
        @param current: The current value.
        @type current: int
        @param min: The minimum value.
        @type current: int
        @param max: The maximum value.
        @type max: int
        """
        return round(float(current - min) / (max - min) * 100)

    @staticmethod
    def percentToParam(percent: int, min: int, max: int) -> int:
        """Convert a percentage to a raw parameter value given the current percentage and the minimum and maximum
        raw parameter values.
        @param percent: The current percentage.
        @type percent: int
        @param min: The minimum raw parameter value.
        @type min: int
        @param max: The maximum raw parameter value.
        @type max: int
        """
        return round(float(percent) / 100 * (max - min) + min)

    def bind(self, event, handler):
        if event not in (EngineEvent.bookmark_reached, EngineEvent.state_changed):
            raise NotImplementedError
        self.event_handlers.setdefault(event, []).append(handler)

