"""Original preservation, cancellation, real codecs and round-trip chapters."""

import os
import subprocess
import wave
from pathlib import Path
from threading import Event

import mutagen
import pytest

from bookworm.audiobooks.exporter import (
    ExportCancelledError,
    ExportOptions,
    export_book,
    save_copy,
    verify_recordings,
)
from bookworm.audiobooks.importer import import_book

native = pytest.mark.skipif(
    os.environ.get("BOOKWORM_TEST_AUDIO") != "1", reason="Native audio tests are opt-in"
)


@pytest.fixture
def source_book(tmp_path):
    folder = tmp_path / "Árvíztűrő, %;! könyv"
    folder.mkdir()
    for name in ("01.wav", "02.wav"):
        with wave.open(str(folder / name), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(22050)
            audio.writeframes(b"\x10\x00" * 22050 * 2)
    return import_book(folder)


def test_copy_is_byte_identical_and_only_contains_recordings(source_book, tmp_path):
    (Path(source_book.root) / "notes.txt").write_text("not audio")
    target = save_copy(source_book, tmp_path / "copy")
    assert sorted(p.name for p in target.iterdir()) == ["01.wav", "02.wav"]
    for source in Path(source_book.root).glob("*.wav"):
        assert (target / source.name).read_bytes() == source.read_bytes()


def test_copy_cancellation_does_not_replace_destination(source_book, tmp_path):
    book = import_book(Path(source_book.root) / "01.wav")
    target = tmp_path / "copy.wav"
    target.write_bytes(b"previous copy")
    cancel = Event()
    with pytest.raises(ExportCancelledError):
        save_copy(book, target, cancel, lambda *_: cancel.set(), overwrite=True)
    assert target.read_bytes() == b"previous copy"
    assert not list(tmp_path.glob(".bookworm-copy-*"))


def test_original_cannot_be_overwritten(source_book):
    source = Path(source_book.root) / "01.wav"
    with pytest.raises(ValueError, match="Original recordings"):
        save_copy(import_book(source), source, overwrite=True)


def test_different_extension_does_not_fake_conversion(source_book, tmp_path):
    book = import_book(Path(source_book.root) / "01.wav")
    with pytest.raises(ValueError, match="extension"):
        save_copy(book, tmp_path / "not-really-an-mp3.mp3")


def test_invalid_mp3_rate_combination():
    with pytest.raises(ValueError, match="160"):
        ExportOptions(sample_rate=22050, bitrate=320)


@native
@pytest.mark.parametrize("format_name", ("mp3", "m4b", "flac", "wav"))
@pytest.mark.parametrize("rate", (0.5, 1, 2))
def test_real_export_format_channels_rate_duration_and_chapters(
    source_book, tmp_path, format_name, rate
):
    options = ExportOptions(format=format_name, sample_rate=22050, channels=1, rate=rate, boost=12)
    target = export_book(source_book, tmp_path / ("output." + format_name), options)
    audio = mutagen.File(target)
    assert audio.info.channels == 1
    assert audio.info.sample_rate == 22050
    assert abs(audio.info.length - 4 / rate) < 0.5
    imported = import_book(target)
    if format_name in ("mp3", "m4b"):
        assert [c.title for c in imported.chapters] == [c.title for c in source_book.chapters]
        assert abs(imported.chapters[1].start_ms - 2000 / rate) <= 1
    if format_name == "mp3":
        assert abs(audio.info.bitrate - 128000) < 1000


@native
def test_real_export_cancellation_removes_only_temporary_files(source_book, tmp_path):
    target = tmp_path / "output.mp3"
    target.write_bytes(b"preserve")
    cancel = Event()

    def progress(_stage, _percent):
        cancel.set()

    with pytest.raises(ExportCancelledError):
        export_book(source_book, target, ExportOptions(), cancel, progress, overwrite=True)
    assert target.read_bytes() == b"preserve"
    assert not list(tmp_path.glob(".bookworm-export-*"))


@native
def test_import_fully_decodes_and_ignores_other_types(source_book):
    root = Path(source_book.root)
    (root / "photo.png").write_bytes(b"not a photo")
    (root / "text.pdf").write_bytes(b"not audio")
    result = import_book(root, verify=True)
    assert len(result.chapters) == 2
    (root / "pretend.mp3").write_bytes(b"%PDF-1.7 not audio")
    with pytest.raises(ValueError, match="pretend.mp3"):
        import_book(root, verify=True)


@native
def test_stereo_48000_export_is_real(source_book, tmp_path):
    target = export_book(
        source_book,
        tmp_path / "stereo.mp3",
        ExportOptions(sample_rate=48000, channels=2, bitrate=192),
    )
    info = mutagen.File(target).info
    assert (info.sample_rate, info.channels, round(info.bitrate / 1000)) == (48000, 2, 192)


@native
def test_mixed_input_formats_and_sample_rates(tmp_path):
    root = tmp_path / "Mixed"
    root.mkdir()
    for name, sample_rate, channels in (("01.mp3", 22050, 1), ("02.flac", 48000, 2)):
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "sine=duration=2",
                "-ar",
                str(sample_rate),
                "-ac",
                str(channels),
                str(root / name),
            ],
            check=True,
        )
    book = import_book(root, verify=True)
    target = export_book(book, tmp_path / "mixed.m4b", ExportOptions(format="m4b"))
    assert abs(mutagen.File(target).info.length - book.duration_ms / 1000) < 0.5


@native
def test_missing_recording_is_reported_before_verification(source_book):
    source_book.absolute_path(1).unlink()
    with pytest.raises(FileNotFoundError):
        verify_recordings(source_book)
