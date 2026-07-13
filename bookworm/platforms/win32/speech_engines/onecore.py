import io
import platform
import queue
import threading
import wave
import weakref
from contextlib import suppress
from dataclasses import dataclass
from functools import partial

import wx
from winrt.windows.media.speechsynthesis import (
    SpeechAppendedSilence,
    SpeechPunctuationSilence,
    SpeechSynthesizer,
)
from winrt.windows.storage.streams import Buffer, InputStreamOptions

from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from bookworm.platforms.win32.nvwave import WavePlayer
from bookworm.speechdriver.element.converter.ssml import SsmlSpeechConverter
from bookworm.speechdriver.engine import BaseSpeechEngine, VoiceInfo
from bookworm.speechdriver.enumerations import EngineEvent, RateSpec, SynthState
from bookworm.speechdriver.utterance import SpeechStyle, SpeechUtterance

from .utils import create_audio_bookmark_name, process_audio_bookmark

log = logger.getChild(__name__)
INVALID_VOICE = "Invalid voice"
INVALID_PITCH = "Invalid pitch"
INVALID_RATE = "Invalid rate"
INVALID_VOLUME = "Invalid volume"
COMPRESSED_AUDIO = "Compressed audio"
RATE_MAP = {
    RateSpec.extra_slow: range(20),
    RateSpec.slow: range(20, 40),
    RateSpec.medium: range(40, 60),
    RateSpec.fast: range(60, 80),
    RateSpec.extra_fast: range(80, 100),
}


class OneCoreSsmlSpeechConverter(SsmlSpeechConverter):
    """OneCore does not support the audio element."""

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
        for handler in synth.event_handlers.get(EngineEvent.state_changed, ()):
            handler(self, state)

    def on_bookmark_reached(self, bookmark):
        if (synth := self.synthref()) is None:
            log.warning(
                "Called on_bookmark_reached method on OneCoreSynth while the synthesizer is dead"
            )
            return
        if not process_audio_bookmark(bookmark):
            for handler in synth.event_handlers.get(EngineEvent.bookmark_reached, ()):
                handler(self, bookmark)


@dataclass(slots=True, frozen=True)
class PlaybackTask:
    audio: bytes
    bookmarks: tuple
    generation: int


def split_audio_at_bookmarks(audio, *, frame_size, frame_rate, bookmarks):
    """Yield PCM segments ending at each bookmark."""
    cursor = 0
    audio_frames = len(audio) // frame_size
    for seconds, name in bookmarks:
        bookmark_frame = min(
            audio_frames,
            max(cursor // frame_size, round(seconds * frame_rate)),
        )
        end = bookmark_frame * frame_size
        yield audio[cursor:end], name
        cursor = end
    yield audio[cursor:], None


def wait_for_async_operation(operation):
    completed = threading.Event()
    operation.completed = lambda _operation, _status: completed.set()
    completed.wait()
    return operation.get_results()


class OcSpeechEngine(BaseSpeechEngine):
    name = "onecore"
    display_name = _("One-core Synthesizer")
    default_rate = 20
    speech_converter = OneCoreSsmlSpeechConverter()

    def __init__(self):
        super().__init__()
        self.event_sink = EventSink(weakref.ref(self))
        self.event_handlers = {}
        self._lock = threading.RLock()
        self._resume_event = threading.Event()
        self._resume_event.set()
        self._task_queue = queue.Queue()
        self._players = {}
        self._player = None
        self._generation = 0
        self._closed = False
        self._rate = 1 / 0.06
        self._rate_spec = RateSpec.medium
        self._pitch = 50
        self._volume = 100
        synthesizer = SpeechSynthesizer()
        try:
            self._voice_id = synthesizer.voice.id
            try:
                _ = synthesizer.options.speaking_rate
            except OSError:
                self._prosody_supported = False
            else:
                self._prosody_supported = True
        finally:
            synthesizer.close()
        self._thread = threading.Thread(
            target=self._run,
            name="OneCore speech",
            daemon=True,
        )
        self._thread.start()

    @classmethod
    def check(cls):
        return platform.version().startswith("10")

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._generation += 1
            self._resume_event.set()
            if self._player is not None:
                self._player.stop()
            self._clear_task_queue()
            self._task_queue.put(None)
            self.event_sink.on_state_changed(SynthState.ready)
        self._thread.join()
        for player in self._players.values():
            player.close()
        self._players.clear()
        self.event_handlers.clear()
        self.event_sink = None

    def get_voices(self):
        return [
            VoiceInfo(
                id=voice.id,
                name=voice.display_name,
                desc=voice.display_name,
                language=LocaleInfo(voice.language),
            )
            for voice in SpeechSynthesizer.all_voices
        ]

    @property
    def state(self):
        return self.event_sink._state

    @property
    def voice(self):
        return next(
            (voice for voice in self.get_voices() if voice.id == self._voice_id),
            None,
        )

    @voice.setter
    def voice(self, value):
        if not any(voice.id == value.id for voice in self.get_voices()):
            raise ValueError(INVALID_VOICE)
        self._voice_id = value.id

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter
    def pitch(self, value):
        if not 0 <= value <= 100:
            raise ValueError(INVALID_PITCH)
        self._pitch = value

    @property
    def rate(self):
        if not self._prosody_supported:
            rate_range = RATE_MAP[self._rate_spec]
            return round((rate_range.start + rate_range.stop) / 2)
        return self._rate

    @rate.setter
    def rate(self, value):
        if not 0 <= value <= 100:
            raise ValueError(INVALID_RATE)
        if self._prosody_supported:
            self._rate = value
        else:
            self._rate_spec = next(
                (rate for rate, rate_range in RATE_MAP.items() if value in rate_range),
                RateSpec.medium,
            )

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        if not 0 <= value <= 100:
            raise ValueError(INVALID_VOLUME)
        self._volume = value

    def preprocess_utterance(self, utterance):
        if not self._prosody_supported:
            styled_utterance = SpeechUtterance()
            with styled_utterance.set_style(SpeechStyle(rate=self.rate)):
                styled_utterance.add(utterance)
            utterance = styled_utterance
        return self.speech_converter.convert(utterance)

    def speak_utterance(self, ssml):
        with self._lock:
            if self._closed:
                return
            generation = self._generation
        audio, bookmarks = self._synthesize(ssml)
        with self._lock:
            if self._closed or generation != self._generation:
                return
            self._generation += 1
            generation = self._generation
            if self._player is not None:
                self._player.stop()
            self._clear_task_queue()
            self._resume_event.set()
            self._task_queue.put(PlaybackTask(audio, bookmarks, generation))
            self.event_sink.on_state_changed(SynthState.busy)

    def stop(self):
        with self._lock:
            if self._closed:
                return
            self._generation += 1
            self._resume_event.set()
            if self._player is not None:
                self._player.stop()
            self._clear_task_queue()
            self.event_sink.on_state_changed(SynthState.ready)

    def pause(self):
        if self.state is not SynthState.busy:
            return
        self._resume_event.clear()
        with self._lock:
            player = self._player
        if player is not None:
            player.pause(True)
        self.event_sink.on_state_changed(SynthState.paused)

    def resume(self):
        if self.state is not SynthState.paused:
            return
        with self._lock:
            player = self._player
        if player is not None:
            player.pause(False)
        self._resume_event.set()
        self.event_sink.on_state_changed(SynthState.busy)

    def bind(self, event, handler):
        if event not in (EngineEvent.bookmark_reached, EngineEvent.state_changed):
            raise NotImplementedError
        self.event_handlers.setdefault(event, []).append(handler)

    def _synthesize(self, ssml):
        synthesizer = SpeechSynthesizer()
        stream = None
        try:
            voice = next(
                (voice for voice in SpeechSynthesizer.all_voices if voice.id == self._voice_id),
                None,
            )
            if voice is not None:
                synthesizer.voice = voice
            options = synthesizer.options
            if self._prosody_supported:
                options.speaking_rate = self._rate * 0.06
            options.audio_pitch = self._pitch / 50
            options.audio_volume = self._volume / 100
            with suppress(AttributeError, OSError):
                options.appended_silence = SpeechAppendedSilence.MIN
                options.punctuation_silence = SpeechPunctuationSilence.MIN
            operation = synthesizer.synthesize_ssml_to_stream_async(ssml)
            try:
                stream = wait_for_async_operation(operation)
            finally:
                with suppress(OSError):
                    operation.close()
            bookmarks = tuple(
                (marker.time.total_seconds(), marker.text)
                for marker in stream.markers
                if marker.media_marker_type == "Speech:Bookmark"
            )
            stream.seek(0)
            buffer = Buffer(stream.size)
            read_operation = stream.read_async(
                buffer,
                stream.size,
                InputStreamOptions.NONE,
            )
            try:
                return bytes(memoryview(wait_for_async_operation(read_operation))), bookmarks
            finally:
                with suppress(OSError):
                    read_operation.close()
        finally:
            if stream is not None:
                stream.close()
            synthesizer.close()

    def _run(self):
        while True:
            task = self._task_queue.get()
            if task is None:
                self._task_queue.task_done()
                return
            try:
                self._play_audio(task)
            except Exception:
                if self._is_current(task.generation):
                    log.exception("Error playing OneCore speech")
            finally:
                self._task_queue.task_done()
            wx.CallAfter(self._finish_if_current, task.generation)

    def _play_audio(self, task):
        with wave.open(io.BytesIO(task.audio), "rb") as wav_file:
            if wav_file.getcomptype() != "NONE":
                raise ValueError(COMPRESSED_AUDIO)
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()
            pcm = wav_file.readframes(wav_file.getnframes())
        player = self._get_or_create_player(channels, frame_rate, sample_width * 8)
        with self._lock:
            if task.generation != self._generation:
                return
            self._player = player
        for segment, bookmark in split_audio_at_bookmarks(
            pcm,
            frame_size=channels * sample_width,
            frame_rate=frame_rate,
            bookmarks=task.bookmarks,
        ):
            self._resume_event.wait()
            if not self._is_current(task.generation):
                return
            callback = (
                partial(self._handle_bookmark, task.generation, bookmark) if bookmark else None
            )
            if segment:
                player.feed(segment, onDone=callback)
            elif callback is not None:
                player.sync()
                callback()
        player.idle()

    def _handle_bookmark(self, generation, bookmark):
        if self._is_current(generation):
            self.event_sink.on_bookmark_reached(bookmark)

    def _finish_if_current(self, generation):
        if self._is_current(generation):
            self.event_sink.on_state_changed(SynthState.ready)

    def _get_or_create_player(self, channels, sample_rate, bits_per_sample):
        key = (channels, sample_rate, bits_per_sample)
        if key not in self._players:
            self._players[key] = WavePlayer(
                channels=channels,
                samplesPerSec=sample_rate,
                bitsPerSample=bits_per_sample,
                buffered=True,
            )
        return self._players[key]

    def _is_current(self, generation):
        with self._lock:
            return not self._closed and generation == self._generation

    def _clear_task_queue(self):
        while True:
            try:
                self._task_queue.get_nowait()
            except queue.Empty:
                return
            else:
                self._task_queue.task_done()
