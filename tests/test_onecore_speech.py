import sys
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

if sys.platform != "win32":
    pytest.skip("OneCore requires Windows", allow_module_level=True)

from bookworm.i18n import LocaleInfo
from bookworm.platforms.win32 import nvwave
from bookworm.platforms.win32.speech_engines import onecore
from bookworm.speechdriver.engine import EngineEvent, SynthState, VoiceInfo
from bookworm.speechdriver.utterance import SpeechUtterance


class FakeWavePlayer:
    def __init__(self, **kwargs):
        self.audio_format = kwargs
        self.audio = bytearray()

    def feed(self, data, **kwargs):
        self.audio.extend(data)
        if callback := kwargs.get("onDone"):
            callback()

    def sync(self):
        pass

    def idle(self):
        pass

    def stop(self):
        pass

    def pause(self, switch):
        pass

    def close(self):
        pass


def test_audio_is_split_at_bookmark_frames():
    segments = list(
        onecore.split_audio_at_bookmarks(
            bytes(range(8)),
            frame_size=2,
            frame_rate=4,
            bookmarks=[(0.25, "first"), (0.75, "second")],
        )
    )

    assert segments == [
        (bytes(range(2)), "first"),
        (bytes(range(2, 6)), "second"),
        (bytes(range(6, 8)), None),
    ]


def test_onecore_ssml_uses_selected_voice_language(monkeypatch):
    engine = object.__new__(onecore.OcSpeechEngine)
    engine._prosody_supported = True
    voice = VoiceInfo("test", "Test", "Test", LocaleInfo("zh-CN"))
    monkeypatch.setattr(engine, "get_voices", lambda: [voice])
    engine.voice = voice
    utterance = SpeechUtterance()
    utterance.add_text("Voice language check")

    assert 'xml:lang="zh-CN"' in engine.preprocess_utterance(utterance)


def test_onecore_synthesizes_ssml_and_dispatches_bookmarks(monkeypatch):
    monkeypatch.setattr(onecore, "WavePlayer", FakeWavePlayer)
    monkeypatch.setattr(onecore.wx, "CallAfter", lambda func, *args: func(*args))

    engine = onecore.OcSpeechEngine()
    ready = threading.Event()
    states = []
    bookmarks = []

    def on_state_changed(_sender, state):
        states.append(state)
        if state is SynthState.ready:
            ready.set()

    engine.bind(
        EngineEvent.state_changed,
        on_state_changed,
    )
    engine.bind(
        EngineEvent.bookmark_reached,
        lambda _sender, bookmark: bookmarks.append(bookmark),
    )
    utterance = SpeechUtterance()
    utterance.add_text("Hello from Bookworm")
    utterance.add_bookmark("test-bookmark")

    try:
        engine.speak(utterance)
        assert ready.wait(10)
        assert states == [SynthState.busy, SynthState.ready]
        assert bookmarks == ["test-bookmark"]
        assert any(player.audio for player in engine._players.values())
    finally:
        engine.close()


def test_stop_discards_speech_that_is_still_synthesizing(monkeypatch):
    monkeypatch.setattr(onecore.wx, "CallAfter", lambda func, *args: func(*args))
    engine = onecore.OcSpeechEngine()
    synthesis_started = threading.Event()
    finish_synthesis = threading.Event()

    def synthesize(_ssml, _generation):
        synthesis_started.set()
        assert finish_synthesis.wait(10)
        return b"", ()

    monkeypatch.setattr(engine, "_synthesize", synthesize)
    play_audio = Mock()
    monkeypatch.setattr(engine, "_play_audio", play_audio)
    utterance = SpeechUtterance()
    utterance.add_text("Discard this speech")

    try:
        engine.speak(utterance)
        assert synthesis_started.wait(10)
        engine.stop()
        finish_synthesis.set()
        engine._task_queue.join()

        assert engine.state is SynthState.ready
        assert engine._task_queue.empty()
        play_audio.assert_not_called()
    finally:
        finish_synthesis.set()
        engine.close()


def test_legacy_rate_uses_the_matching_ssml_rate():
    engine = object.__new__(onecore.OcSpeechEngine)
    engine._prosody_supported = False
    engine._rate_spec = onecore.RateSpec.medium
    engine._voice_id = "test"
    engine.get_voices = lambda: [
        VoiceInfo("test", "Test", "Test", LocaleInfo("en-US"))
    ]
    utterance = SpeechUtterance()
    utterance.add_text("Legacy rate check")
    engine.rate = 100

    assert 'rate="x-fast"' in engine.preprocess_utterance(utterance)


def test_voice_probe_closes_temporary_onecore_engine():
    before = sum(thread.name == "OneCore speech" for thread in threading.enumerate())

    onecore.OcSpeechEngine.get_first_available_voice()

    after = sum(thread.name == "OneCore speech" for thread in threading.enumerate())
    assert after == before


def test_failed_wave_player_stop_clears_stopping_state(monkeypatch):
    monkeypatch.setattr(nvwave.WavePlayer, "__del__", lambda _self: None)
    player = object.__new__(nvwave.WavePlayer)
    player._minBufferSize = 0
    player._lock = threading.RLock()
    player._waveout_lock = threading.RLock()
    player._global_waveout_lock = threading.RLock()
    player._waveout = 1
    player._waveout_event = object()
    player._prev_whdr = object()
    player._prevOnDone = object()
    player._safe_winmm_call = lambda *_args: False
    monkeypatch.setattr(
        nvwave,
        "windll",
        SimpleNamespace(kernel32=SimpleNamespace(SetEvent=lambda _event: None)),
    )

    player.stop()

    assert player._prev_whdr is None
    assert player._prevOnDone is None
