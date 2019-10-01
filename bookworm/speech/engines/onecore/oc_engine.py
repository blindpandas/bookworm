# coding: utf-8

import platform
import clr
import System
from weakref import ref
from pathlib import Path
from bookworm.speech.enumerations import EngineEvent, SynthState, RateSpec
from bookworm.speech.engine import BaseSpeechEngine, VoiceInfo
from bookworm.logger import logger

try:
    _oc_dll = Path.cwd().joinpath("OcSpeechEngine.dll")
    clr.AddReference(str(_oc_dll))
    from OcSpeechEngine import OcSpeechEngine as _OnecoreEngine
    from .oc_utterance import OcSpeechUtterance
    _oc_available = True
except:
    _oc_available = False


log = logger.getChild(__name__)


class OcSpeechEngine(BaseSpeechEngine):

    name = "onecore"
    display_name = _("One-core Synthesizer")

    def __init__(self):
        super().__init__()
        self.synth = _OnecoreEngine()
        self._rate = 0
        self.synth.BookmarkReached += self._on_bookmark_reached
        self.synth.StateChanged += self._on_state_changed
        self.__event_handlers = {}

    @classmethod
    def check(self):
        return platform.version().startswith("10") and _oc_available

    def close(self):
        self.synth.BookmarkReached -= self._on_bookmark_reached
        self.synth.StateChanged -= self._on_state_changed
        self.synth.Finalize()

    def get_voices(self):
        rv = []
        for voice in self.synth.GetVoices():
            rv.append(
                VoiceInfo(
                    id=voice.Id,
                    name=voice.Name,
                    desc=voice.Description,
                    language=voice.Language,
                    data={"voice_obj": voice}
                )
            )
        return rv

    @property
    def state(self):
        return SynthState(self.synth.State)

    @property
    def voice(self):
        for voice in self.get_voices():
            if voice.id == self.synth.Voice.Id:
                return voice

    @voice.setter
    def voice(self, value):
        try:
            self.synth.Voice = value.data["voice_obj"]
        except System.InvalidOperationException:
            raise ValueError(f"Can not set voice to  {value}.")

    @property
    def rate(self):
        return self._rate

    def rate_to_spec(self):
        if 0 <= self._rate <= 20:
            return RateSpec.extra_slow
        elif 21 <= self._rate <= 40:
            return RateSpec.slow
        elif 41 <= self._rate <= 60:
            return RateSpec.medium
        elif 61 <= self._rate <= 80:
            return RateSpec.fast
        elif 81 <= self._rate <= 100:
            return RateSpec.fast

    @rate.setter
    def rate(self, value):
        if 0 <= self._rate <= 100:
            self._rate = value
        else:
            raise ValueError("The provided rate is out of range")

    @property
    def volume(self):
        return int(self.synth.Volume)

    @volume.setter
    def volume(self, value):
        try:
            self.synth.Volume = float(value)
        except:
            raise ValueError("The provided volume level is out of range")

    def speak_utterance(self, utterance):
        self.synth.SpeakAsync(utterance)

    def preprocess_utterance(self, utterance):
        oc_utterance = OcSpeechUtterance(ref(self))
        oc_utterance.populate_from_speech_utterance(utterance)
        return oc_utterance.to_oc_prompt()

    def stop(self):
        self.synth.CancelSpeech()

    def pause(self):
        self.synth.Pause()

    def resume(self):
        self.synth.Resume()

    def bind(self, event, handler):
        if event not in (EngineEvent.bookmark_reached, EngineEvent.state_changed):
            raise NotImplementedError
        self.__event_handlers.setdefault(event, []).append(handler)

    def _on_bookmark_reached(self, sender, arg):
        handlers = self.__event_handlers.get(EngineEvent.bookmark_reached, ())
        for handler in handlers:
            handler(self, arg)

    def _on_state_changed(self, sender, arg):
        handlers = self.__event_handlers.get(EngineEvent.state_changed, ())
        for handler in handlers:
            handler(self, SynthState(arg))
