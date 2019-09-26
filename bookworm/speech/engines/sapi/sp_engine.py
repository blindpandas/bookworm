# coding: utf-8

import System
from System.Globalization import CultureInfo
from System.Speech import Synthesis
from functools import partial
from collections import OrderedDict
from contextlib import suppress
from bookworm.speech.enumerations import EngineEvents, SynthState
from bookworm.speech.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speech.utterance import SpeechStyle
from bookworm.i18n.lang_locales import locale_map
from bookworm.logger import logger
from .sp_utterance import SapiSpeechUtterance


log = logger.getChild(__name__)


class SapiSpeechEngine(BaseSpeechEngine):
    """Our Pythonic Interface to SAPI speech enginge."""

    name = "sapi"
    display_name = _("Microsoft Speech API Version 5")
    utterance_cls = SapiSpeechUtterance

    def __init__(self, language=None):
        super().__init__(language)
        self.synth = Synthesis.SpeechSynthesizer()
        self.synth.SetOutputToDefaultAudioDevice()
        self._event_table = {}
        self.__events = {}

    @classmethod
    def check(self):
        return True

    def close(self):
        with suppress(System.ObjectDisposedException):
            self.stop()
        self._unregister_events()
        self.synth.Dispose()
        self.synth.Finalize()

    def get_voices(self, language=None):
        rv = []
        voices = []
        if language is not None:
            current_culture = CultureInfo.CurrentCulture
            if current_culture.IetfLanguageTag.startswith(language.lower()):
                voices.extend(self.synth.GetInstalledVoices(current_culture))
            if language in locale_map:
                for locale in locale_map[language]:
                    culture = CultureInfo.GetCultureInfoByIetfLanguageTag(
                        f"{language}-{locale}"
                    )
                    voices.extend(self.synth.GetInstalledVoices(culture))
            voices.extend(self.synth.GetInstalledVoices(CultureInfo(language)))
        else:
            voices = self.synth.GetInstalledVoices()
        if not voices:
            log.warning("No suitable TTS voice was found.")
            return rv
        for voice in voices:
            if not voice.Enabled:
                continue
            info = voice.VoiceInfo
            rv.append(
                VoiceInfo(
                    id=info.Id,
                    name=info.Name,
                    desc=info.Description,
                    language=info.Culture.IetfLanguageTag,
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
            if voice.name == self.synth.Voice.Name:
                return voice

    @voice.setter
    def voice(self, value):
        try:
            self.synth.SelectVoice(value.name)
        except System.ArgumentException:
            raise ValueError(f"Can not set voice to  {value}.")

    @property
    def rate(self):
        return self.synth.Rate

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

    def speak(self, utterance):
        super().speak(utterance)
        # We need to wrap the whol utterance in another
        # one that sets the voice. Because The Speak()
        # function does not honor  the engine voice.
        voice_utterance = SapiSpeechUtterance()
        with voice_utterance.set_style(SpeechStyle(voice=self.voice)):
            voice_utterance.add(utterance)
        self.synth.SpeakAsync(voice_utterance.prompt)

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
        if  event in self._event_table:
            if handler in self._event_table[event]:
                return
            else:
                self._event_table[event].append(handler)
                return
        self._event_table.setdefault(event, []).append(handler)
        if event is EngineEvents.state_changed:
            self.synth.StateChanged += self._on_state_changed
            self.__events[self.synth.StateChanged] = self._on_state_changed
        elif event is EngineEvents.bookmark_reached:
            func = partial(self._handle_sapi_events, EngineEvents.bookmark_reached, "Bookmark")
            self.synth.BookmarkReached += func
            self.__events[self.synth.BookmarkReached] = func
        else:
            raise NotImplementedError

    def _handle_sapi_events(self, event, attr, sender, args):
        for handler in self._event_table[event]:
            handler(getattr(args, attr))

    def _on_state_changed(self, sender, args):
        for handler in self._event_table[EngineEvents.state_changed]:
            handler(SynthState(sender.State))

    def _unregister_events(self):
        for delegate, func in self.__events.items():
            delegate -= func
        self.__events.clear()

