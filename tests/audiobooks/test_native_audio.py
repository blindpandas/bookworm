"""Opt-in decoder/DSP tests: BOOKWORM_TEST_AUDIO=1, libmpv and FFmpeg required.

PCM capture tests the actual audio engine without a sound card or listening to
test tones. Spectral/peak checks do not certify subjective speech quality.
"""

import os
import queue
import shutil
import subprocess
import time
import wave

import pytest

from bookworm.audiobooks.backend import MpvAudioBackend
from bookworm.audiobooks.importer import import_book

pytestmark = pytest.mark.skipif(
    os.environ.get("BOOKWORM_TEST_AUDIO") != "1", reason="Native audio tests are opt-in"
)


def render(tmp_path, rate, boost, amplitude=0.2):
    import numpy as np

    sample_rate = 48000
    samples = np.sin(2 * np.pi * 440 * np.arange(4 * sample_rate) / sample_rate) * amplitude
    source = tmp_path / "input.wav"
    with wave.open(str(source), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes((samples * 32767).astype("<i2").tobytes())
    output = tmp_path / "output.wav"
    events = queue.Queue()
    finished = False
    backend = MpvAudioBackend(lambda *args: events.put(args), ao="pcm", ao_pcm_file=str(output))

    def loaded():
        assert backend.set_rate(rate)
        assert backend.set_boost(boost)
        backend.play()

    def ended():
        nonlocal finished
        finished = True

    def error(message):
        pytest.fail(message)

    try:
        backend.load(source, loaded, ended, error, rate=rate, boost=boost)
        deadline = time.monotonic() + 20
        while not finished and time.monotonic() < deadline:
            try:
                callback, *args = events.get(timeout=0.1)
                callback(*args)
            except queue.Empty:
                pass
        assert finished, "Audio render timed out"
    finally:
        backend.close()
    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(output),
            "-f",
            "f32le",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    return np.frombuffer(result.stdout, dtype="<f4"), sample_rate


@pytest.mark.parametrize("rate", [0.5, 0.75, 1.0, 1.25, 1.5, 2.0])
def test_actual_engine_preserves_pitch_and_changes_duration(tmp_path, rate):
    import numpy as np

    signal, sample_rate = render(tmp_path, rate, 0)
    assert abs(len(signal) / sample_rate - 4 / rate) < 0.15
    middle = signal[sample_rate // 2 : -sample_rate // 2]
    spectrum = np.abs(np.fft.rfft(middle * np.hanning(len(middle))))
    frequency = np.fft.rfftfreq(len(middle), 1 / sample_rate)[np.argmax(spectrum)]
    assert abs(frequency - 440) < 2


@pytest.mark.parametrize("rate", [0.75, 1, 1.5])
def test_maximum_boost_has_headroom_even_on_loud_input(tmp_path, rate):
    import numpy as np

    signal, _ = render(tmp_path, rate, 12, amplitude=0.95)
    assert np.isfinite(signal).all()
    assert np.max(np.abs(signal)) <= 0.893
    assert np.max(np.abs(signal)) >= 0.7


def test_boost_makes_quiet_audio_louder(tmp_path):
    import numpy as np

    base = tmp_path / "base"
    amplified = tmp_path / "amplified"
    base.mkdir()
    amplified.mkdir()
    original, _ = render(base, 1, 0, amplitude=0.02)
    boosted, _ = render(amplified, 1, 12, amplitude=0.02)
    ratio = np.sqrt(np.mean(boosted**2)) / np.sqrt(np.mean(original**2))
    assert 3.8 < ratio < 4.1


def test_actual_mp3_and_m4b_metadata_and_chapters(tmp_path):
    from mutagen.id3 import CHAP, TIT2
    from mutagen.mp3 import MP3

    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg is unavailable")
    mp3 = tmp_path / "voice.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=4",
            "-q:a",
            "4",
            str(mp3),
        ],
        check=True,
    )
    audio = MP3(mp3)
    audio.tags.add(
        CHAP(
            element_id="intro",
            start_time=0,
            end_time=2000,
            sub_frames=[TIT2(text=["Első fejezet"])],
        )
    )
    audio.tags.add(
        CHAP(
            element_id="next",
            start_time=2000,
            end_time=4000,
            sub_frames=[TIT2(text=["Második fejezet"])],
        )
    )
    audio.save()
    book = import_book(mp3)
    assert [c.title for c in book.chapters] == ["Első fejezet", "Második fejezet"]
    assert book.chapters[1].start_ms == 2000
    metadata = tmp_path / "metadata.txt"
    metadata.write_text(
        ";FFMETADATA1\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=2000\n"
        "title=First\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=2000\nEND=4000\ntitle=Second\n"
    )
    m4b = tmp_path / "book.m4b"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(mp3),
            "-i",
            str(metadata),
            "-map_metadata",
            "1",
            "-map_chapters",
            "1",
            "-c:a",
            "aac",
            str(m4b),
        ],
        check=True,
    )
    imported = import_book(m4b)
    assert [c.title for c in imported.chapters] == ["First", "Second"]
    assert imported.chapters[1].start_ms == 2000


def test_quicktime_only_m4b_chapters(tmp_path):
    source = tmp_path / "quicktime.m4b"
    metadata = tmp_path / "chapters.txt"
    metadata.write_text(
        ";FFMETADATA1\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=1000\ntitle=First\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=1000\nEND=2000\ntitle=Second\n"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=duration=2",
            "-i",
            str(metadata),
            "-map_metadata",
            "1",
            "-map_chapters",
            "1",
            "-movflags",
            "disable_chpl",
            "-c:a",
            "aac",
            str(source),
        ],
        check=True,
    )
    book = import_book(source)
    assert [c.title for c in book.chapters] == ["First", "Second"]
    assert book.chapters[1].start_ms == 1000


@pytest.mark.parametrize("suffix", ("wav", "mp3", "m4b"))
@pytest.mark.parametrize("rate", (0.5, 1, 2))
def test_exact_seek_is_verified_before_resume(tmp_path, suffix, rate):
    source = tmp_path / ("seek." + suffix)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=10", str(source)], check=True
    )
    events = queue.Queue()
    backend = MpvAudioBackend(lambda *args: events.put(args), ao="null")
    errors = []
    try:
        backend.load(
            source, lambda: backend.seek(3141), lambda: None, errors.append, rate=rate, boost=12
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                callback, *args = events.get(timeout=0.02)
                callback(*args)
            except queue.Empty:
                pass
            if backend.control and backend._pending_seek is None and backend.position() is not None:
                if abs(backend.position() - 3141) <= 50:
                    break
        assert not errors
        assert abs(backend.position() - 3141) <= 50
        assert backend.control.pause
        started = time.monotonic()
        for target in (2345, 6789, 1234):
            backend.seek(target)
        while backend._pending_seek is not None and time.monotonic() - started < 3:
            try:
                callback, *args = events.get(timeout=0.02)
                callback(*args)
            except queue.Empty:
                pass
        assert not errors
        assert abs(backend.position() - 1234) <= 50
        assert time.monotonic() - started < 1
    finally:
        backend.close()
