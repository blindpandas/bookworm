# coding: utf-8

import platform
import clr
import System
from weakref import ref
from functools import partial
from bookworm.speech.enumerations import EngineEvent, SynthState, RateSpec
from bookworm.speech.engine import BaseSpeechEngine, VoiceInfo
from bookworm.logger import logger
from .oc_utterance import OcSpeechUtterance


try:
    clr.AddReference("OcSpeechEngine")
    from OcSpeechEngine import OcSpeechEngine as _OnecoreEngine
    _oc_available = True
except:
    __oc_available = False


log = logger.getChild(__name__)


class OcSpeechEngine(BaseSpeechEngine):

    name = "onecore"
    display_name = _("One-core Synthesizer")

    def __init__(self, language=None):
        self._language = language
        self.synth = _OnecoreEngine()
        self._rate = 0
        self._event_table = {}
        self.__events = {}

    @classmethod
    def check(self):
        return platform.version().startswith("10") and _oc_available

    def close(self):
        self._unregister_events()
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
        """Return engine-specific speech utterance (if necessary)."""
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
        if event in self._event_table:
            if handler in self._event_table[event]:
                return
            else:
                self._event_table[event].append(handler)
                return
        self._event_table.setdefault(event, []).append(handler)
        if event is EngineEvent.state_changed:
            func = partial(self._handle_sapi_events, EngineEvent.state_changed, arg_transform=lambda state: SynthState(state))
            self.synth.StateChanged += func
            self.__events[self.synth.StateChanged] = func
        elif event is EngineEvent.bookmark_reached:
            func = partial(self._handle_sapi_events, EngineEvent.bookmark_reached)
            self.synth.BookmarkReached += func
            self.__events[self.synth.BookmarkReached] = func
        else:
            raise NotImplementedError

    def _handle_sapi_events(self, event, sender, args, arg_transform=None):
        for handler in self._event_table[event]:
            if arg_transform is not None:
                args = arg_transform(args)
            handler(args)

    def _unregister_events(self):
        for delegate, func in self.__events.items():
            delegate -= func
        self.__events.clear()


