"""Exercise the real SQLite writer under blocked I/O, errors and close barriers."""

import time
import wave
from threading import Event
from unittest.mock import Mock

import pytest

from bookworm.audiobooks.importer import import_book
from bookworm.audiobooks.player import AudiobookPlayer, State
from bookworm.audiobooks.storage import AudioLibrary


@pytest.fixture
def store(tmp_path):
    source = tmp_path / "source.wav"
    with wave.open(str(source), "wb") as audio:
        audio.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\0\0" * 8000 * 5)
    book = import_book(source)
    path = tmp_path / "library.sqlite3"
    library = AudioLibrary(path, defer_positions=True)
    library.add(book)
    yield library, book, path
    library.close(discard_positions=True)


def test_slow_disk_does_not_block_submissions_and_latest_values_are_readable(store, monkeypatch):
    library, book, path = store
    writer = library.position_writer
    entered, release = Event(), Event()
    persist = writer._persist
    batches = []

    def blocked(connection, updates):
        batches.append(updates)
        entered.set()
        assert release.wait(5), "Test did not release the blocked writer"
        persist(connection, updates)

    monkeypatch.setattr(writer, "_persist", blocked)
    try:
        library.save_position(book, 100, 1, 1)
        assert entered.wait(2)
        started = time.monotonic()
        for position in range(200, 1201, 100):
            library.save_position(book, position, 0.75, 0.8, boost=3)
        assert time.monotonic() - started < 0.25
        assert library.state(book.id) == dict(
            position=1200, rate=0.75, volume=0.8, completed=0, boost=3
        )
    finally:
        release.set()
    library.flush_positions()
    assert len(batches) == 2  # Initial write, then one coalesced latest value.
    reopened = AudioLibrary(path)
    try:
        assert reopened.state(book.id)["position"] == 1200
    finally:
        reopened.close()


def test_background_failure_is_reported_once_but_flush_never_claims_success(store, monkeypatch):
    library, book, _path = store
    failed = Event()

    def fail(_connection, _updates):
        failed.set()
        raise OSError("disk full")

    monkeypatch.setattr(library.position_writer, "_persist", fail)
    library.save_position(book, 1234, 1, 1)
    assert failed.wait(2)
    # The worker stores the failure before exiting; join is deterministic.
    library.position_writer.thread.join(timeout=2)
    with pytest.raises(OSError, match="disk full"):
        library.check_position_errors()
    library.check_position_errors()
    with pytest.raises(OSError, match="disk full"):
        library.flush_positions()
    with pytest.raises(OSError, match="disk full"):
        library.save_position(book, 2000, 1, 1)


def test_close_flushes_exact_zero_before_reopening(store):
    library, book, path = store
    library.save_position(book, 4500, 1.5, 0.6, True, 6)
    library.save_position(book, 0, 1.5, 0.6, False, 6)
    library.close()
    library.close()  # Idempotent teardown.
    reopened = AudioLibrary(path)
    try:
        assert reopened.state(book.id) == dict(
            position=0, rate=1.5, volume=0.6, completed=0, boost=6
        )
    finally:
        reopened.close()


def test_backup_includes_pending_position_and_bookmarks(store, tmp_path):
    library, book, _path = store
    library.bookmark(book, 321, "Test bookmark")
    library.save_position(book, 2345, 1, 1)
    backup = tmp_path / "backup.sqlite3"
    library.backup(backup)
    restored = AudioLibrary(backup)
    try:
        assert restored.state(book.id)["position"] == 2345
        assert restored.bookmarks(book.id)[0]["position"] == 321
    finally:
        restored.close()


def test_failed_close_is_not_reported_as_durable(store, monkeypatch):
    library, book, path = store

    def fail(_connection, _updates):
        raise OSError("write failed")

    monkeypatch.setattr(library.position_writer, "_persist", fail)
    library.save_position(book, 1234, 1, 1)
    with pytest.raises(OSError, match="write failed"):
        library.close()
    assert not library.position_writer.thread.is_alive()
    reopened = AudioLibrary(path)
    try:
        assert reopened.state(book.id)["position"] == 0
    finally:
        reopened.close()


def test_player_stops_and_reports_background_save_error_once(store, monkeypatch):
    library, book, _path = store
    backend = Mock()
    backend.position.return_value = 0
    messages = []
    player = AudiobookPlayer(backend, library, error_notify=messages.append)
    player.open(book)
    backend.load.call_args.args[1]()
    player.play()

    def fail(_connection, _updates):
        raise OSError("disk full")

    monkeypatch.setattr(library.position_writer, "_persist", fail)
    player.seek(1234)
    library.position_writer.thread.join(timeout=2)
    player.poll()
    assert player.state is State.ERROR and not player.desired_play
    assert len(messages) == 1 and "listening position could not be saved" in messages[0]
    player.poll()
    assert len(messages) == 1
    player.close(save=False)
