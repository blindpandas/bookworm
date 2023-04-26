# coding: utf-8

import weakref
from pathlib import Path

from bookworm.paths import data_path
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from bookworm.speechdriver.element.converter.ssml import SsmlSpeechConverter
from bookworm.speechdriver.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speechdriver.enumerations import (EngineEvent, RateSpec,
                                                SynthState)
from bookworm.speechdriver.utterance import SpeechUtterance

from .tts_system import PiperTextToSpeechSystem
from .speechplayer import PiperSpeechPlayer, PlayerState
from ..utils import create_audio_bookmark_name, process_audio_bookmark

log = logger.getChild(__name__)

PLAYER_STATE_TO_SYNTH_STATE = {
    PlayerState.STOPPED: SynthState.ready,
    PlayerState.PLAYING: SynthState.busy,
    PlayerState.PAUSED: SynthState.paused
}


class PiperTTSSsmlSpeechConverter(SsmlSpeechConverter):
    """Piper synthesizer does not support the audio element."""

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
            handler(self, PLAYER_STATE_TO_SYNTH_STATE[state])

    def on_bookmark_reached(self, bookmark):
        if (synth := self.synthref()) is None:
            log.warning(
                "Called on_bookmark_reached method on synth while the synthesizer is dead"
            )
            return
        if not process_audio_bookmark(bookmark):
            for handler in synth.event_handlers.get(EngineEvent.bookmark_reached, ()):
                handler(self, bookmark)

    def log(self, message, level):
        log.log(level, message)


class PiperSpeechEngine(BaseSpeechEngine):
    name = "piper"
    display_name = _("Piper Neural TTS")
    default_rate = 50
    speech_converter = PiperTTSSsmlSpeechConverter()

    def __init__(self):
        super().__init__()
        self.event_sink = EventSink(weakref.ref(self))
        self.event_handlers = {}
        voices = PiperTextToSpeechSystem.load_voices_from_directory(get_piper_voices_directory())
        self.tts = PiperTextToSpeechSystem(voices)
        self.player = PiperSpeechPlayer(
            self.tts,
            state_change_callback=self.event_sink.on_state_changed,
            bookmark_callback=self.event_sink.on_bookmark_reached
        )

    @classmethod
    def check(self):
        return any(PiperTextToSpeechSystem.load_voices_from_directory(get_piper_voices_directory()))

    def close(self):
        super().close()
        self.event_handlers.clear()
        self.event_sink = None
        self.player.close()

    def get_voices(self):
        rv = []
        for voice in self.tts.get_voices():
            voice_locale = LocaleInfo(voice.language)
            voice_quality = voice.properties["quality"]
            rv.append(
                VoiceInfo(
                    id=voice.key,
                    name=voice.name,
                    desc=f"{voice.name}, {voice_locale.english_name} ({voice_quality})",
                    language=voice_locale,
                )
            )
        return rv

    @property
    def state(self):
        return PLAYER_STATE_TO_SYNTH_STATE[self.player.get_state()]

    @property
    def voice(self):
        for voice in self.get_voices():
            if voice.id == self.tts.voice:
                return voice

    @voice.setter
    def voice(self, value):
        self.tts.voice = value.id

    @property
    def pitch(self):
        return 50

    @pitch.setter
    def pitch(self, value):
        pass

    @property
    def rate(self):
        return self.tts.rate

    @rate.setter
    def rate(self, value):
        self.tts.rate = value

    @property
    def volume(self):
        return self.tts.volume

    @volume.setter
    def volume(self, value):
        self.tts.volume = value

    def preprocess_utterance(self, utterance):
        return self.speech_converter.convert(utterance)

    def speak_utterance(self, utterance):
        self.player.speak_ssml(utterance)

    def stop(self):
        self.player.stop()

    def pause(self):
        self.player.pause()

    def resume(self):
        self.player.resume()

    def bind(self, event, handler):
        if event not in (EngineEvent.bookmark_reached, EngineEvent.state_changed):
            raise NotImplementedError
        self.event_handlers.setdefault(event, []).append(handler)



def get_piper_voices_directory():
    piper_voices_path = data_path("piper", "voices")
    piper_voices_path.mkdir(parents=True, exist_ok=True)
    return piper_voices_path