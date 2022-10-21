# coding: utf-8

import clr
import System
from System.Globalization import CultureInfo
from bookworm.platforms.win32.runtime import reference_gac_assembly

reference_gac_assembly("System.Speech\*\System.Speech.dll")
from System.Speech import Synthesis
from .sp_utterance import SapiSpeechUtterance




from enum import IntEnum
from collections import OrderedDict
import comtypes.client
from comtypes import COMError
import winreg
import weakref

from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.speechdriver.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speechdriver.enumerations import EngineEvent, SynthState
from bookworm.speechdriver.utterance import SpeechStyle
from bookworm.logger import logger



log = logger.getChild(__name__)


class SPAudioState(IntEnum):
    # https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms720596(v=vs.85)
    Closed = 0
    Stopped = 1
    Paused = 2
    Running = 3


class SpeechVoiceSpeakFlags(IntEnum):
    # https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms720892(v=vs.85)
    Async = 1
    PurgeBeforeSpeak = 2
    IsXML = 8


class SpeechVoiceEvents(IntEnum):
    # https://msdn.microsoft.com/en-us/previous-versions/windows/desktop/ms720886(v=vs.85)
    StartInputStream = 2
    EndInputStream = 4
    Bookmark = 16


class SapiEventSink(object):
    """Handles SAPI event notifications.
    See https://msdn.microsoft.com/en-us/library/ms723587(v=vs.85).aspx
    """

    def __init__(self, synthRef: weakref.ReferenceType):
        self.synthRef = synthRef

    def StartStream(self, streamNum, pos):
        synth = self.synthRef()
        if synth is None:
            log.warning(
                "Called StartStream method on SapiSink while the synthesizer is dead"
            )
        else:
            for handler in synth.event_handlers.get(EngineEvent.state_changed, ()):
                handler(SynthState.busy)

    def Bookmark(self, streamNum, pos, bookmark, bookmarkId):
        synth = self.synthRef()
        if synth is None:
            log.warning(
                "Called Bookmark method on SapiSink while the synthesizer is dead"
            )
        else:
            for handler in synth.event_handlers.get(EngineEvent.bookmark_reached, ()):
                handler(bookmark)

    def EndStream(self, streamNum, pos):
        synth = self.synthRef()
        if synth is None:
            log.warning("Called stream end method on EndStream while the synthesizer is dead")
        else:
            for handler in synth.event_handlers.get(EngineEvent.state_changed, ()):
                handler(SynthState.ready)



class SapiSpeechEngine(BaseSpeechEngine):
    name = "sapi5"
    display_name = "Microsoft Speech API version 5 (SAPI 5}"
    default_rate = 50
    default_volume = 75
    COM_CLASS: t.ClassVar = "SAPI.SPVoice"

    @classmethod
    def check(cls):
        try:
            r = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, cls.COM_CLASS)
            r.Close()
            return True
        except:
            return False

    def __init__(self):
        super().__init__()
        self.event_handlers = {}
        self._tts_audio_stream = None
        self._pitch = 50
        self.tts = comtypes.client.CreateObject(self.COM_CLASS)
        self._events_connection = comtypes.client.GetEvents(
            self.tts, SapiEventSink(weakref.ref(self))
        )
        self.tts.EventInterests = (
            SpeechVoiceEvents.StartInputStream
            | SpeechVoiceEvents.Bookmark
            | SpeechVoiceEvents.EndInputStream
        )

    def close(self):
        self._events_connection = None
        self._tts = None
        super().close()

    def get_voices(self):
        v = self._get_voice_tokens()
        retval = []
        for i in range(len(v)):
            try:
                id = v[i].Id
                name = v[i].GetDescription()
                try:
                    language = v[i].getattribute("language").split(";")[0]
                except KeyError:
                    language = "en"
            except COMError:
                log.warning("Could not get the voice info. Skipping...")
            retval.append(VoiceInfo(
                id=id,
                name=name,
                desc=name,
                language=LocaleInfo(language)
            ))
        return retval

    @property
    def voice(self):
        return more_itertools.first_true(
            voices := self.get_voices(),
            pred=lambda v: v.id == self.tts.voice.Id,
            default=voices[0]
        )

    @voice.setter
    def voice(self, value):
        tokens = self.get_voice_token()
        for i in range(len(tokens)):
            voice = tokens[i]
            if value.id == voice.Id:
                self.tts.voice = voice
                break

    @property
    def rate(self):
        return (self.tts.rate * 5) + 50

    @rate.setter
    def rate(self, value):
        self.tts.Rate = self._percentToRate(value)

    @property
    def volume(self):
        return self.tts.volume

    @volume.setter
    def volume(self, value):
        self.tts.Volume = value

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter 
    def pitch(self, value):
        self._pitch = value

    def speak_utterance(self, utterance):
        # We need to wrap the whole utterance in another
        # one that sets the voice. Because The Speak()
        # function does not honor  the engine voice.
        voice_utterance = SapiSpeechUtterance()
        voice_utterance.prompt.Culture = CultureInfo.GetCultureInfoByIetfLanguageTag(
            self.voice.language.ietf_tag
        )
        with voice_utterance.set_style(SpeechStyle(voice=self.voice)):
            voice_utterance.append_utterance(utterance)
        flags = SpeechVoiceSpeakFlags.IsXML | SpeechVoiceSpeakFlags.Async
        self.tts.Speak(voice_utterance.prompt.ToXml(), flags)

    def stop(self):
        self.tts.Speak(
            None, SpeechVoiceSpeakFlags.Async | SpeechVoiceSpeakFlags.PurgeBeforeSpeak
        )

    def pause(self):
        self.tts.Pause()
        for handler in synth.event_handlers.get(EngineEvent.state_changed, ()):
            handler(SynthState.paused)

    def resume(self):
        self.tts.Resume()
        for handler in synth.event_handlers.get(EngineEvent.state_changed, ()):
            handler(SynthState.busy)

    def preprocess_utterance(self, utterance):
        sp_utterance = SapiSpeechUtterance()
        sp_utterance.populate_from_speech_utterance(utterance)
        return sp_utterance

    def bind(self, event, handler):
        """Bind a member of `EngineEvents` enum to a handler."""
        if event not in (EngineEvent.bookmark_reached, EngineEvent.state_changed):
            raise NotImplementedError
        self.event_handlers.setdefault(event, []).append(handler)

    def _get_voice_tokens(self):
        """Provides a collection of sapi5 voice tokens. Can be overridden by subclasses if tokens should be looked for in some other registry location."""
        return self.tts.getVoices()

    def _percentToRate(self, percent):
        return (percent - 50) // 5

    def _percentToPitch(self, percent):
        return percent // 2 - 25
