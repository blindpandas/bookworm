# coding: utf-8


import locale
import winreg
import weakref
from enum import IntEnum
from collections import OrderedDict

import comtypes.client
import more_itertools
from comtypes import COMError
from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.speechdriver.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speechdriver.enumerations import EngineEvent, SynthState
from bookworm.speechdriver.utterance import SpeechUtterance, SpeechStyle
from bookworm.logger import logger
from ..utils import process_audio_bookmark
from .COM_interfaces.SpeechLib import ISpAudio
from .element_converter import sapi_speech_converter


log = logger.getChild(__name__)


class SPAudioState(IntEnum):
    # https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms720596(v=vs.85)
    Closed = 0
    Stopped = 1
    Paused = 2
    Running = 3

    def as_synth_state(self) -> SynthState:
        if self in (SPAudioState.Closed, SPAudioState.Stopped):
            return SynthState.ready
        elif self is SPAudioState.Running:
            return SynthState.busy
        elif self is SPAudioState.Paused:
            return SynthState.paused


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
    """
    Handles SAPI event notifications.
    See https://msdn.microsoft.com/en-us/library/ms723587(v=vs.85).aspx
    """

    def __init__(self, synthref: weakref.ReferenceType):
        self.synthref = synthref

    def StartStream(self, streamNum, pos):
        synth = self.synthref()
        if synth is None:
            log.warning(
                "Called StartStream method on SapiSink while the synthesizer is dead"
            )
        else:
            synth._set_state(SynthState.busy)

    def Bookmark(self, streamNum, pos, bookmark, bookmarkId):
        synth = self.synthref()
        if synth is None:
            log.warning(
                "Called Bookmark method on SapiSink while the synthesizer is dead"
            )
            return
        if not process_audio_bookmark(bookmark):
            for handler in synth.event_handlers.get(EngineEvent.bookmark_reached, ()):
                handler(synth, bookmark)

    def EndStream(self, streamNum, pos):
        synth = self.synthref()
        if synth is None:
            log.warning("Called stream end method on EndStream while the synthesizer is dead")
        else:
            synth._set_state(SynthState.ready)


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
        self.__state = SynthState.ready
        self.event_handlers = {}
        self._voice_token = None
        self.__pitch = 50
        self._init_tts()

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
                    language=locale.windows_locale[int(v[i].getattribute('language').split(';')[0],16)]
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
    def state(self):
        return self.__state

    @property
    def voice(self):
        return more_itertools.first_true(
            voices := self.get_voices(),
            pred=lambda v: v.id == self.tts.voice.Id,
            default=voices[0]
        )

    @voice.setter
    def voice(self, value):
        tokens = self._get_voice_tokens()
        for i in range(len(tokens)):
            voice = tokens[i]
            if value.id == voice.Id:
                self._voice_token = voice
                break
        self._init_tts()

    @property
    def rate(self):
        return (self.tts.rate * 5) + 50

    @rate.setter
    def rate(self, value):
        self.tts.Rate = sapi_speech_converter._percentToRate(value)

    @property
    def volume(self):
        return self.tts.volume

    @volume.setter
    def volume(self, value):
        self.tts.Volume = value

    @property
    def pitch(self):
        return self.__pitch

    @pitch.setter 
    def pitch(self, value):
        self.__pitch = value

    def preprocess_utterance(self, utterance):
        voice_utterance = SpeechUtterance()
        style = SpeechStyle(
            pitch=self.pitch
        )
        with voice_utterance.set_style(style):
            voice_utterance.add(utterance)
        # SAPI5 does not raise bookmark events if the bookmark is the last element of the content 
        # thus, add a little scilence to force raising that bookmark event
        voice_utterance.add_pause(5)
        return voice_utterance

    def speak_utterance(self, utterance):
        sapi_xml = sapi_speech_converter.convert(utterance, localeinfo=None)
        flags = SpeechVoiceSpeakFlags.IsXML | SpeechVoiceSpeakFlags.Async
        self.tts.Speak(sapi_xml, flags)

    def stop(self):
        if self.state is SynthState.paused:
            self.resume()
        self.tts.Speak(
            "", SpeechVoiceSpeakFlags.Async | SpeechVoiceSpeakFlags.PurgeBeforeSpeak
        )
        self._set_state(SynthState.ready)

    def pause(self):
        if self.state is SynthState.busy:
            self._pause_switch(True)
            self._set_state(SynthState.paused)

    def resume(self):
        if self.state is SynthState.paused:
            self._pause_switch(False)
            self._set_state(SynthState.busy)

    def bind(self, event, handler):
        """Bind a member of `EngineEvents` enum to a handler."""
        if event not in (EngineEvent.bookmark_reached, EngineEvent.state_changed):
            raise NotImplementedError
        self.event_handlers.setdefault(event, []).append(handler)

    def _set_state(self, new_state: SynthState):
        self.__state = new_state
        for handler in self.event_handlers.get(EngineEvent.state_changed, ()):
            handler(self, new_state)

    def _init_tts(self):
        self.tts = comtypes.client.CreateObject(self.COM_CLASS)
        if self._voice_token:
            self.tts.voice = self._voice_token
        self._events_connection = comtypes.client.GetEvents(
            self.tts, SapiEventSink(weakref.ref(self))
        )
        # You can handle sentence and word boundry info here
        self.tts.EventInterests = (
            SpeechVoiceEvents.StartInputStream
            | SpeechVoiceEvents.Bookmark
            | SpeechVoiceEvents.EndInputStream
        )
        try:
            self.tts_audio_stream =self.tts.audioOutputStream.QueryInterface(ISpAudio)
        except COMError:
            log.warning("SAPI5 voice does not support ISPAudio") 
            self.tts_audio_stream=None

    def _get_voice_tokens(self):
        return self.tts.getVoices()

    def _pause_switch(self, switch: bool):
        if self.tts_audio_stream:
            oldState = self.tts_audio_stream.GetStatus().State
            if switch and oldState == SPAudioState.Running:
                # pausing
                self.tts_audio_stream.setState(SPAudioState.Paused, 0)
            elif not switch and oldState == SPAudioState.Paused:
                # unpausing
                self.tts_audio_stream.setState(SPAudioState.Running, 0)
        else:
            if switch:
                self.tts.Pause()
            else:
                self.tts.Resume()
