# coding: utf-8

from collections import deque
from platform import win32_ver
from contextlib import suppress
from unsync import unsync
from bookworm.speech.enumerations import EngineEvents, SynthState
from bookworm.speech.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speech.utterance import SpeechStyle
from bookworm.i18n.lang_locales import locale_map
from bookworm.logger import logger
from .oc_utterance import OnecoreSpeechUtterance, OcBookmark

try:
    from winrt.windows.media.speechsynthesis import SpeechSynthesizer
    from winrt.windows.media.playback import MediaPlayer
    from winrt.windows.media.playback import MediaPlaybackState
    from winrt.windows.storage.streams import InMemoryRandomAccessStream
    _winrt_available = True
except:
    _winrt_available = False


log = logger.getChild(__name__)


class OnecoreSpeechEngine(BaseSpeechEngine):
    """Our Pythonic Interface to OneCore speech synthesizer."""

    utterance_cls = OnecoreSpeechUtterance

    def __init__(self, language=None):
        super().__init__(language)
        self.synth = SpeechSynthesizer()
        self.player = MediaPlayer()
        self.player.auto_play = True
        self._evt_stch_id = self.player.playback_session.add_playback_state_changed(self._on_playback_state_changed)
        self._evt_mend_id = self.player.add_media_ended(lambda p, o: self._start_speech())
        self._speech_queue = deque()
        self._event_table = {}

    @classmethod
    def check(self):
        return (win32_ver()[0] == '10') and _winrt_available

    def close(self):
        self.synth.close()
        #self.player.remove_media_ended(self._evt_mend_id)
        #self.player.playback_session.remove_playback_state_changed(self._evt_stch_id)
        self.player.close()
        self.synth = self.player = None
        self._event_table.clear()

    def get_voices(self, language=None):
        rv = []
        voices = self.synth.get_all_voices()
        for voice in voices:
            rv.append(VoiceInfo(
                id=voice.id,
                name=voice.display_name,
                desc=voice.description,
                language=voice.language,
                data={"voice_obj": voice}
            ))
        return rv

    @property
    def state(self):
        state = self.player.playback_session.playback_state
        if state in (MediaPlaybackState.BUFFERING, MediaPlaybackState.PLAYING, MediaPlaybackState.OPENING):
            return SynthState.busy
        elif state  == MediaPlaybackState.PAUSED:
            return SynthState.paused
        else:
            return SynthState.ready

    @property
    def voice(self):
        for voice in self.get_voices():
            if voice.id == self.synth.voice.id:
                return voice

    @voice.setter
    def voice(self, value):
        self.synth.voice = value.data["voice_obj"]

    @property
    def rate(self):
        return 100

    @rate.setter
    def rate(self, value):
        pass

    @property
    def volume(self):
        return 100

    @volume.setter
    def volume(self, value):
        pass

    def speak(self, utterance):
        super().speak(utterance)
        self._speech_queue.extend(utterance.get_speech_sequence())
        if self.state is SynthState.ready:
            self._start_speech()

    def stop(self):
        if self.state is not SynthState.ready:
            self.player.pause()
            self.player.set_stream_source(InMemoryRandomAccessStream())

    def pause(self):
        if self.state is SynthState.busy:
            self.player.pause()

    def resume(self):
        if self.state is SynthState.paused:
            self.player.play()

    def bind(self, event, handler):
        if event in self._event_table:
            if handler in self._event_table[event]:
                return
            else:
                return self._event_table[event].append(handler)
        self._event_table.setdefault(event, []).append(handler)

    def _on_playback_state_changed(self, playback_session, args):
        handlers = self._event_table.get(EngineEvents.state_changed, [])
        for func in handlers:
            func(self, self.state)

    def _start_speech(self):
        self.player.set_stream_source(InMemoryRandomAccessStream())
        if self._speech_queue:
            nextup = self._speech_queue.popleft()
            if type(nextup) is OcBookmark:
                bhandlers = self._event_table.get(EngineEvents.bookmark_reached, [])
                for func in bhandlers:
                    func(nextup.bookmark)
                self._start_speech()
            else:
                self._synthesize_text(nextup)

    @unsync
    async def _synthesize_text(self, text):
        stream = await self.synth.synthesize_ssml_to_stream_async(text)
        self.player.set_stream_source(stream)
