import threading

from bookworm.platforms.win32.speech_engines import onecore
from bookworm.speechdriver.engine import EngineEvent, SynthState
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
    engine = onecore.OcSpeechEngine()
    synthesis_started = threading.Event()
    finish_synthesis = threading.Event()

    def synthesize(_ssml):
        synthesis_started.set()
        assert finish_synthesis.wait(10)
        return b"", ()

    monkeypatch.setattr(engine, "_synthesize", synthesize)
    utterance = SpeechUtterance()
    utterance.add_text("Discard this speech")
    speaker = threading.Thread(target=engine.speak, args=(utterance,))

    try:
        speaker.start()
        assert synthesis_started.wait(10)
        engine.stop()
        finish_synthesis.set()
        speaker.join(10)

        assert not speaker.is_alive()
        assert engine.state is SynthState.ready
        assert engine._task_queue.empty()
    finally:
        finish_synthesis.set()
        speaker.join(10)
        engine.close()
        engine.stop()
