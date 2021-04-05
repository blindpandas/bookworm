# coding: utf-8

import System
from System.Globalization import CultureInfo
from contextlib import suppress
from bookworm.i18n import LocaleInfo
from bookworm.platform_services._win32.runtime import reference_gac_assembly
from bookworm.speechdriver.enumerations import EngineEvent, SynthState
from bookworm.speechdriver.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speechdriver.utterance import SpeechStyle
from bookworm.logger import logger

log = logger.getChild(__name__)


_sapi_available = False
try:
    reference_gac_assembly("System.Speech\*\System.Speech.dll")
    from System.Speech import Synthesis
    from .sp_utterance import SapiSpeechUtterance

    _sapi_available = True
except OSError as e:
    log.error(f"Could not load Sapi5 speech engine: {e}")


class SapiSpeechEngine(BaseSpeechEngine):
    """Our Pythonic Interface to SAPI speech engine."""

    name = "sapi"
    display_name = _("Microsoft Speech API Version 5")

    def __init__(self):
        super().__init__()
        self.synth = Synthesis.SpeechSynthesizer()
        self.synth.SetOutputToDefaultAudioDevice()
        self.synth.BookmarkReached += self._on_bookmark_reached
        self.synth.StateChanged += self._on_state_changed
        self.__event_handlers = {}

    @classmethod
    def check(self):
        return _sapi_available

    def close(self):
        with suppress(System.ObjectDisposedException):
            self.stop()
        self.synth.BookmarkReached -= self._on_bookmark_reached
        self.synth.StateChanged -= self._on_state_changed
        self.synth.Dispose()
        self.synth.Finalize()

    def get_voices(self, language=None):
        rv = []
        for voice in self.synth.GetInstalledVoices():
            if not voice.Enabled:
                continue
            info = voice.VoiceInfo
            if (voice_culture := info.Culture) is not None:
                voice_language = LocaleInfo(voice_culture.IetfLanguageTag)
            else:
                log.exception(
                    f"Failed to obtain culture information for voice {info.Name}"
                )
                continue
            rv.append(
                VoiceInfo(
                    id=info.Id,
                    name=info.Name,
                    desc=info.Description,
                    language=voice_language,
                    gender=info.Gender,
                    age=info.Age,
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
            self.synth.SelectVoice(value.name)
        except System.ArgumentException:
            raise ValueError(f"Can not set voice to  {value}.")

    @property
    def rate(self):
        return (self.synth.Rate * 5) + 50

    @rate.setter
    def rate(self, value):
        if not (0 <= value <= 100):
            raise ValueError(f"Value {value} for rate is out of range.")
        self.synth.Rate = (value - 50) / 5

    @property
    def volume(self):
        return self.synth.Volume

    @volume.setter
    def volume(self, value):
        if not (0 <= value <= 100):
            raise ValueError(f"Value {value} for volume is out of range.")
        self.synth.Volume = value

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
        self.synth.SpeakAsync(voice_utterance.prompt)

    def preprocess_utterance(self, utterance):
        sp_utterance = SapiSpeechUtterance()
        sp_utterance.populate_from_speech_utterance(utterance)
        return sp_utterance

    def stop(self):
        if self.state is not SynthState.ready:
            if self.state is SynthState.paused:
                self.synth.Resume()
            self.synth.SpeakAsyncCancelAll()

    def pause(self):
        if self.state is SynthState.busy:
            self.synth.Pause()

    def resume(self):
        if self.state is SynthState.paused:
            self.synth.Resume()

    def bind(self, event, handler):
        if event not in (EngineEvent.bookmark_reached, EngineEvent.state_changed):
            raise NotImplementedError
        self.__event_handlers.setdefault(event, []).append(handler)

    def _on_bookmark_reached(self, sender, args):
        handlers = self.__event_handlers.get(EngineEvent.bookmark_reached, ())
        for handler in handlers:
            handler(self, args.Bookmark)

    def _on_state_changed(self, sender, args):
        handlers = self.__event_handlers.get(EngineEvent.state_changed, ())
        for handler in handlers:
            handler(self, SynthState(sender.State))
