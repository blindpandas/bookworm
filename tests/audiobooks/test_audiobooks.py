"""Run independently with pytest --confcutdir=tests/audiobooks tests/audiobooks.

These tests do not initialize the Windows document reader or its OCR libraries.
"""

import json
import os
import shutil
import sqlite3
import subprocess
import wave
from dataclasses import replace
from threading import Event

import pytest

from bookworm.audiobooks.importer import ImportCancelledError, import_book, relocate_book
from bookworm.audiobooks.model import Audiobook, Chapter, format_time, parse_time
from bookworm.audiobooks.player import AudiobookPlayer, State
from bookworm.audiobooks.storage import AudioLibrary


def write_wave(path, seconds=2):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\0\0" * (8000 * seconds))
    return path


@pytest.fixture
def book(tmp_path):
    folder = tmp_path / "Árvíztűrő könyv"
    folder.mkdir()
    write_wave(folder / "2.wav", 2)
    write_wave(folder / "10.wav", 3)
    return import_book(folder)


@pytest.fixture
def library(tmp_path, book):
    store = AudioLibrary(tmp_path / "audio.sqlite3")
    store.add(book)
    yield store
    store.close()


class FakeBackend:
    def __init__(self):
        self.loads = []
        self.value = 0
        self.playing = False
        self.rate_supported = True
        self.seek_supported = True
        self.volume = 1
        self.rate = 1

    def load(self, path, ready, finished, error, **settings):
        self.loads.append((path, ready, finished, error))

    def ready(self):
        self.loads[-1][1]()

    def finish(self):
        self.loads[-1][2]()

    def close(self):
        self.playing = False

    def seek(self, value):
        self.value = value
        return self.seek_supported

    def position(self):
        return self.value

    def play(self):
        self.playing = True
        return True

    def pause(self):
        self.playing = False
        return True

    def set_rate(self, rate):
        if self.rate_supported:
            self.rate = rate
        return self.rate_supported

    def set_boost(self, boost):
        self.boost = boost
        return True

    def set_volume(self, volume):
        self.volume = volume
        return True


@pytest.fixture
def setup_player(library, book):
    backend = FakeBackend()
    clock = [100.0]
    messages = []
    player = AudiobookPlayer(backend, library, messages.append, lambda: clock[0])
    player.open(book, 0)
    backend.ready()
    return player, backend, clock, messages


def test_natural_order_and_unicode(book):
    assert [c.path for c in book.chapters] == ["2.wav", "10.wav"]
    assert book.title == "Árvíztűrő könyv"
    assert book.duration_ms == 5000


def test_book_timeline_boundaries(book):
    assert book.locate(-1) == (0, 0)
    assert book.locate(1999) == (0, 1999)
    assert book.locate(2000) == (1, 0)
    assert book.locate(999999) == (1, 3000)
    assert Audiobook.from_dict(book.to_dict()) == book


@pytest.mark.parametrize(
    "path",
    [
        "../escape.mp3",
        "/tmp/escape.mp3",
        "/escape.mp3",
        "//server/share/a.mp3",
        "C:/a.mp3",
        "C:a.mp3",
        "..\\a.mp3",
        "\\escape.mp3",
        "folder/../../a.mp3",
    ],
)
def test_relative_chapter_paths_only(path):
    with pytest.raises(ValueError):
        Chapter(path, "bad", 0, 1000, 1, "x")


@pytest.mark.parametrize(
    "value,expected",
    [
        ("01:02:03", 3723000),
        ("125", 125000),
        ("2:05", 125000),
        ("0", 0),
        ("1.5", 1500),
        ("01:02:03.456", 3723456),
        ("1:03,007", 63007),
    ],
)
def test_time_parser(value, expected):
    assert parse_time(value) == expected


@pytest.mark.parametrize("value", ["-1", "1:60", "1:60:00", "1:2:3:4", "NaN", "", "1.5555", "1e4"])
def test_invalid_times(value):
    with pytest.raises(ValueError):
        parse_time(value)


def test_long_book_time_format():
    assert format_time(100 * 3600 * 1000) == "100:00:00"


def test_cancel_import_is_atomic(tmp_path):
    write_wave(tmp_path / "one.wav")
    cancel = Event()
    cancel.set()
    with pytest.raises(ImportCancelledError):
        import_book(tmp_path, cancel)


def test_corrupt_file_does_not_silently_skip_chapter(tmp_path):
    write_wave(tmp_path / "1.wav")
    (tmp_path / "2.mp3").write_bytes(b"not audio")
    with pytest.raises(ValueError, match="2.mp3"):
        import_book(tmp_path)


def test_missing_empty_and_unreadable_files_are_distinguished(tmp_path, monkeypatch):
    from pathlib import Path

    from bookworm.audiobooks.importer import check_audio_file

    path = tmp_path / "missing.mp3"
    with pytest.raises(FileNotFoundError, match="moved or deleted"):
        import_book(path)
    path.touch()
    with pytest.raises(ValueError, match="0 bytes"):
        import_book(path)
    path.write_bytes(b"readable header")

    def denied(*args, **kwargs):
        raise PermissionError

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(PermissionError, match="Access.*denied"):
        check_audio_file(path)


def test_inaccessible_subfolder_is_not_silently_skipped(tmp_path, monkeypatch):
    from bookworm.audiobooks import importer

    def walk(source, *, onerror, followlinks):
        onerror(PermissionError(13, "Access denied", str(source / "disc2")))
        return iter(())

    monkeypatch.setattr(importer.os, "walk", walk)
    with pytest.raises(OSError, match="disc2"):
        import_book(tmp_path)


def test_folder_links_do_not_import_recordings_from_another_book(tmp_path):
    folder = tmp_path / "this book"
    folder.mkdir()
    write_wave(folder / "own.wav")
    other = tmp_path / "another book"
    other.mkdir()
    write_wave(other / "other.wav")
    link = folder / "linked disc"
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(other)], check=True, capture_output=True
        )
    else:
        link.symlink_to(other, target_is_directory=True)
    imported = import_book(folder)
    assert [chapter.path for chapter in imported.chapters] == ["own.wav"]


def test_reimport_after_timestamp_change_retains_position_and_bookmarks(book, library):
    library.save_position(book, 1257, 1.25, 0.8)
    marker = library.bookmark(book, 1234, "Exact position")
    source = book.absolute_path(0)
    stat = source.stat()
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000000000))
    updated = library.add(import_book(book.root))
    assert updated.id == book.id
    assert len(library.books()) == 1
    assert library.state(book.id)["position"] == 1257
    assert library.bookmarks(book.id)[0]["id"] == marker
    assert updated.chapters[0].mtime_ns == source.stat().st_mtime_ns


def test_duplicate_import_preserves_position_and_notes(library, book):
    library.save_position(book, 2500, 1.25, 0.7)
    library.bookmark(book, 1200, "Név", "Árvíztűrő megjegyzés")
    duplicate = library.add(replace(book, id="different"))
    assert duplicate.id == book.id
    assert len(library.books()) == 1
    assert library.state(book.id)["position"] == 2500
    assert library.bookmarks(book.id)[0]["note"] == "Árvíztűrő megjegyzés"


def test_relocate_preserves_identity_and_validates_recording(book, tmp_path):
    destination = tmp_path / "moved"
    shutil.copytree(book.root, destination)
    moved = relocate_book(book, destination)
    assert moved.id == book.id
    assert moved.absolute_path(0) == destination / "2.wav"
    (destination / "2.wav").write_bytes(b"changed")
    with pytest.raises(ValueError):
        relocate_book(book, destination)


def test_bookmark_export_import_is_idempotent(library, book):
    library.bookmark(book, 2500, "Bookmark", "Note")
    exported = library.export_bookmarks(book)
    assert library.import_bookmarks(book, exported) == 0
    library.remove_bookmark(library.bookmarks(book.id)[0]["id"])
    assert library.import_bookmarks(book, exported) == 1
    assert library.bookmarks(book.id)[0]["position"] == 2500


def test_bookmark_import_validates_all_before_writing(library, book):
    payload = json.loads(library.export_bookmarks(book))
    payload["bookmarks"] = [
        dict(position=100, title="ok", note=""),
        dict(position=-1, title="bad", note=""),
    ]
    with pytest.raises(ValueError):
        library.import_bookmarks(book, json.dumps(payload))
    assert library.bookmarks(book.id) == []


def test_backup_is_a_valid_database_and_remove_keeps_audio(library, book, tmp_path):
    path = tmp_path / "backup.sqlite3"
    library.save_position(book, 1000, 1, 1)
    library.backup(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT position FROM books").fetchone()[0] == 1000
    library.remove(book.id)
    assert book.absolute_path(0).exists()


def test_play_pause_and_saved_progress(setup_player, library, book):
    player, backend, clock, _ = setup_player
    player.play()
    backend.value = 1234
    clock[0] += 6
    player.poll()
    assert library.state(book.id)["position"] == 1234
    player.pause()
    assert player.state is State.PAUSED
    assert not backend.playing


def test_short_and_long_seek_cross_file_boundaries(setup_player):
    player, backend, _, _ = setup_player
    player.play()
    player.skip(3000)
    backend.ready()
    assert player.chapter_index == 1
    assert backend.value == 1000
    assert backend.playing
    player.skip(-2500)
    backend.ready()
    assert player.chapter_index == 0
    assert backend.value == 500


def test_old_native_events_cannot_advance_new_load(setup_player):
    player, backend, _, _ = setup_player
    old_ready, old_finished = backend.loads[0][1:3]
    player.seek(3000)
    old_ready()
    old_finished()
    assert player.state is State.LOADING
    assert player.position_ms == 3000
    backend.ready()
    assert player.state is State.PAUSED


def test_pause_during_loading_prevents_autoplay(setup_player):
    player, backend, _, _ = setup_player
    player.play()
    player.seek(3000)
    player.pause()
    backend.ready()
    assert not backend.playing
    assert player.state is State.PAUSED


def test_eof_advances_and_final_eof_marks_complete(setup_player, library, book):
    player, backend, _, _ = setup_player
    player.play()
    backend.finish()
    assert player.chapter_index == 1
    backend.ready()
    backend.finish()
    assert player.state is State.FINISHED
    assert player.position_ms == 5000
    assert library.state(book.id)["completed"] == 1


def test_sleep_timer_uses_wall_time_not_playback_rate(setup_player):
    player, backend, clock, _ = setup_player
    player.set_rate(1.5)
    player.play()
    player.set_sleep(1)
    clock[0] += 60
    player.poll()
    assert player.state is State.PAUSED
    assert not backend.playing


def test_sleep_at_chapter_does_not_play_next_file(setup_player):
    player, backend, _, _ = setup_player
    player.play()
    player.set_sleep(end_of_chapter=True)
    backend.finish()
    backend.ready()
    assert not backend.playing
    assert player.position_ms == 2000


def test_ab_repeat_across_file_boundary(setup_player):
    player, backend, _, _ = setup_player
    player.set_loop(1000, 3500)
    player.play()
    player.seek(3000)
    backend.ready()
    backend.value = 1600
    player.poll()
    backend.ready()
    assert player.position_ms == 1000
    assert backend.value == 1000


def test_rate_error_is_not_saved_as_success(setup_player, library, book):
    player, backend, _, _ = setup_player
    backend.rate_supported = False
    with pytest.raises(ValueError):
        player.set_rate(1.25)
    assert player.rate == library.state(book.id)["rate"] == 1


def test_load_timeout_is_recoverable(setup_player):
    player, backend, clock, messages = setup_player
    player.seek(3000)
    clock[0] += 21
    player.poll()
    assert player.state is State.ERROR
    assert "timed out" in messages[-1]
    player.play()
    backend.ready()
    assert player.state is State.PLAYING


def test_resume_is_clamped_and_completed_book_does_not_restart(setup_player, library, book):
    player, backend, _, _ = setup_player
    player.seek(1000)
    backend.ready()
    player.close()
    player.open(book, rewind_ms=5000)
    assert player.position_ms == 0
    backend.ready()
    player.seek(book.duration_ms)
    player.close()
    player.open(book)
    player.play()
    assert player.state is State.FINISHED


def test_disk_failure_pauses_and_retains_last_saved_position(setup_player, library, monkeypatch):
    player, backend, clock, messages = setup_player
    player.play()
    backend.value = 1000
    clock[0] += 6

    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(library, "save_position", fail)
    player.poll()
    assert player.state is State.ERROR
    assert not backend.playing
    assert "disk full" in messages[-1]


def test_same_file_chapters_do_not_reload_decoder(tmp_path):
    path = write_wave(tmp_path / "one.wav", 5)
    chapter = Chapter("one.wav", "First", 0, 2000, path.stat().st_size, "test")
    book = Audiobook(
        "one",
        "One book",
        "",
        str(tmp_path),
        (chapter, replace(chapter, title="Second", start_ms=2000, end_ms=5000)),
    )
    library = AudioLibrary(tmp_path / "one.sqlite3")
    library.add(book)
    backend = FakeBackend()
    player = AudiobookPlayer(backend, library)
    player.open(book, 0)
    backend.ready()
    player.play()
    backend.value = 2100
    player.poll()
    assert player.chapter_index == 1
    assert len(backend.loads) == 1
    player.poll()
    assert player.position_ms == 2100
    player.close()
    library.close()
