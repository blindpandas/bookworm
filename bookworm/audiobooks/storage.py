"""Transactional audiobook library, resume positions and time-based annotations."""

import json
import math
import sqlite3
import time
from dataclasses import replace
from pathlib import Path
from threading import Condition, Thread
from uuid import uuid4

from .model import Audiobook

_POSITION_SQL = """UPDATE books SET position=?, rate=?, volume=?, completed=?, updated=?, boost=?
                   WHERE id=?"""


class _PositionWriter:
    """One worker owns its SQLite connection; pending updates coalesce per book.

    The main thread can read the latest submitted values immediately. Flush is
    a durability barrier for closing, switching books and making backups.
    A failed write is surfaced once by the GUI timer and always by flush/save.
    """

    def __init__(self, path):
        self.path = path
        self.condition = Condition()
        self.pending = {}
        self.latest = {}
        self.submitted = self.completed = 0
        self.error = None
        self.error_reported = False
        self.stopping = False
        self.thread = Thread(target=self._run, name="audiobook-position-writer", daemon=True)
        self.thread.start()

    def submit(self, values):
        with self.condition:
            if self.error is not None:
                self.error_reported = True
                raise self.error
            if self.stopping:
                raise RuntimeError("The audiobook position writer is closed")
            self.submitted += 1
            update = self.submitted, values
            self.pending[values[-1]] = update
            self.latest[values[-1]] = update
            self.condition.notify_all()

    def overlay(self, book_id):
        with self.condition:
            item = self.latest.get(book_id)
            if item is None:
                return None
            values = item[1]
            return dict(
                zip(
                    ("position", "rate", "volume", "completed", "boost"),
                    (values[0], values[1], values[2], values[3], values[5]),
                )
            )

    def _persist(self, connection, updates):
        with connection:
            connection.executemany(_POSITION_SQL, [values for _sequence, values in updates])

    def _run(self):
        connection = None
        try:
            connection = sqlite3.connect(self.path, timeout=10)
            while True:
                with self.condition:
                    self.condition.wait_for(lambda: self.pending or self.stopping)
                    if self.stopping and not self.pending:
                        break
                    updates = list(self.pending.values())
                    self.pending.clear()
                self._persist(connection, updates)
                with self.condition:
                    for sequence, values in updates:
                        if self.latest.get(values[-1], (None,))[0] == sequence:
                            del self.latest[values[-1]]
                    self.completed = max(self.completed, *(s for s, _values in updates))
                    self.condition.notify_all()
        except Exception as exc:
            with self.condition:
                self.error = exc
                self.condition.notify_all()
        finally:
            if connection is not None:
                connection.close()

    def check_error(self):
        with self.condition:
            if self.error is not None and not self.error_reported:
                self.error_reported = True
                raise self.error

    def flush(self):
        with self.condition:
            target = self.submitted
            self.condition.wait_for(
                lambda: self.completed >= target or self.error is not None or self.stopping
            )
            if self.error is not None:
                self.error_reported = True
                raise self.error
            if self.completed < target:
                raise RuntimeError("Pending audiobook positions were discarded")

    def close(self, discard=False):
        with self.condition:
            if self.stopping:
                return
        try:
            if not discard:
                self.flush()
        finally:
            with self.condition:
                self.stopping = True
                if discard:
                    self.pending.clear()
                self.condition.notify_all()
            self.thread.join()


class AudioLibrary:
    def __init__(self, path, *, defer_positions=False):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1, 2):
            self.db.close()
            raise ValueError("This audiobook library requires a newer Bookworm version")
        with self.db:
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS books (
                    id TEXT PRIMARY KEY, manifest TEXT NOT NULL,
                    position INTEGER NOT NULL DEFAULT 0,
                    rate REAL NOT NULL DEFAULT 1.0,
                    volume REAL NOT NULL DEFAULT 1.0,
                    completed INTEGER NOT NULL DEFAULT 0,
                    updated REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id TEXT PRIMARY KEY,
                    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
                    position INTEGER NOT NULL, title TEXT NOT NULL, note TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS bookmarks_by_book ON bookmarks(book_id, position);
            """)
            columns = {row[1] for row in self.db.execute("PRAGMA table_info(books)")}
            if "boost" not in columns:
                self.db.execute("ALTER TABLE books ADD COLUMN boost REAL NOT NULL DEFAULT 0")
            self.db.execute("PRAGMA user_version=2")
        self.position_writer = _PositionWriter(path) if defer_positions else None
        self.closed = False

    def close(self, *, discard_positions=False):
        if self.closed:
            return
        try:
            if self.position_writer is not None:
                self.position_writer.close(discard=discard_positions)
        finally:
            self.db.close()
            self.closed = True

    def flush_positions(self):
        if self.position_writer is not None:
            self.position_writer.flush()

    def check_position_errors(self):
        if self.position_writer is not None:
            self.position_writer.check_error()

    def books(self):
        return [
            Audiobook.from_dict(json.loads(row[0]))
            for row in self.db.execute("SELECT manifest FROM books ORDER BY updated DESC")
        ]

    def add(self, book):
        # Reimporting the same source must not reset its bookmarks or position.
        for existing in self.books():
            if existing.root == book.root and tuple(
                replace(chapter, mtime_ns=0) for chapter in existing.chapters
            ) == tuple(replace(chapter, mtime_ns=0) for chapter in book.chapters):
                refreshed = replace(existing, chapters=book.chapters)
                self.update_manifest(refreshed)
                return refreshed
        with self.db:
            self.db.execute(
                "INSERT INTO books(id, manifest, updated) VALUES (?, ?, ?)",
                (book.id, json.dumps(book.to_dict(), ensure_ascii=False), time.time()),
            )
        return book

    def update_manifest(self, book):
        with self.db:
            self.db.execute(
                "UPDATE books SET manifest=?, updated=? WHERE id=?",
                (json.dumps(book.to_dict(), ensure_ascii=False), time.time(), book.id),
            )

    def update_file(self, path, size, signature, mtime_ns):
        """Refresh all references after an audio-preserving tag edit, atomically."""
        path = Path(path).resolve()
        books = self.books()
        with self.db:
            for book in books:
                chapters = tuple(
                    replace(c, size=size, fingerprint=signature, mtime_ns=mtime_ns)
                    if book.absolute_path(i) == path
                    else c
                    for i, c in enumerate(book.chapters)
                )
                if chapters != book.chapters:
                    self.db.execute(
                        "UPDATE books SET manifest=? WHERE id=?",
                        (
                            json.dumps(
                                replace(book, chapters=chapters).to_dict(), ensure_ascii=False
                            ),
                            book.id,
                        ),
                    )

    def remove(self, book_id):
        self.flush_positions()
        with self.db:
            self.db.execute("DELETE FROM books WHERE id=?", (book_id,))

    def state(self, book_id):
        # Capture an outstanding submission before reading: if the worker
        # commits meanwhile, this snapshot is still at least as new as SQLite.
        pending = self.position_writer.overlay(book_id) if self.position_writer else None
        row = self.db.execute(
            "SELECT position, rate, volume, completed, boost FROM books WHERE id=?", (book_id,)
        ).fetchone()
        if row is None:
            raise KeyError(book_id)
        return pending if pending is not None else dict(row)

    def save_position(self, book, position, rate, volume, completed=False, boost=0):
        if not math.isfinite(rate) or not 0.5 <= rate <= 2:
            raise ValueError("Invalid playback rate")
        if not math.isfinite(volume) or not 0 <= volume <= 1:
            raise ValueError("Invalid volume")
        if not math.isfinite(boost) or not 0 <= boost <= 12:
            raise ValueError("Invalid speech boost")
        values = (
            max(0, min(int(position), book.duration_ms)),
            rate,
            volume,
            int(completed),
            time.time(),
            boost,
            book.id,
        )
        if self.position_writer is not None:
            self.position_writer.submit(values)
        else:
            with self.db:
                self.db.execute(_POSITION_SQL, values)

    def bookmark(self, book, position, title, note="", bookmark_id=None):
        if not title.strip():
            raise ValueError(_("A bookmark needs a name."))
        bookmark_id = bookmark_id or uuid4().hex
        with self.db:
            self.db.execute(
                """INSERT INTO bookmarks(id, book_id, position, title, note)
                VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET
                title=excluded.title, note=excluded.note WHERE bookmarks.book_id=excluded.book_id""",
                (
                    bookmark_id,
                    book.id,
                    max(0, min(int(position), book.duration_ms)),
                    title.strip(),
                    note,
                ),
            )
        return bookmark_id

    def bookmarks(self, book_id):
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT * FROM bookmarks WHERE book_id=? ORDER BY position, id", (book_id,)
            )
        ]

    def remove_bookmark(self, bookmark_id):
        with self.db:
            self.db.execute("DELETE FROM bookmarks WHERE id=?", (bookmark_id,))

    def export_bookmarks(self, book):
        return json.dumps(
            {
                "format": "bookworm-audio-bookmarks",
                "version": 1,
                "book_id": book.id,
                "title": book.title,
                "duration_ms": book.duration_ms,
                "chapters": [[c.path, c.start_ms, c.end_ms, c.fingerprint] for c in book.chapters],
                "bookmarks": self.bookmarks(book.id),
            },
            ensure_ascii=False,
            indent=2,
        )

    def import_bookmarks(self, book, text):
        payload = json.loads(text)
        chapters = [[c.path, c.start_ms, c.end_ms, c.fingerprint] for c in book.chapters]
        saved_chapters = payload.get("chapters")
        same_book_after_tag_edit = (
            payload.get("book_id") == book.id
            and isinstance(saved_chapters, list)
            and all(isinstance(c, list) and len(c) == 4 for c in saved_chapters)
            and [c[:3] for c in saved_chapters] == [c[:3] for c in chapters]
        )
        if (
            payload.get("format") != "bookworm-audio-bookmarks"
            or payload.get("version") != 1
            or payload.get("duration_ms") != book.duration_ms
            or (saved_chapters != chapters and not same_book_after_tag_edit)
        ):
            raise ValueError(_("The bookmark file does not belong to this audiobook."))
        entries = payload.get("bookmarks")
        if not isinstance(entries, list) or len(entries) > 100000:
            raise ValueError(_("Invalid bookmark file."))
        checked = []
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or type(entry.get("position")) is not int
                or not 0 <= entry["position"] <= book.duration_ms
                or not isinstance(entry.get("title"), str)
                or not entry["title"].strip()
                or not isinstance(entry.get("note"), str)
            ):
                raise ValueError(_("Invalid bookmark file."))
            checked.append((entry["position"], entry["title"], entry["note"]))
        existing = {(b["position"], b["title"], b["note"]) for b in self.bookmarks(book.id)}
        added = 0
        with self.db:
            for entry in checked:
                if entry not in existing:
                    self.db.execute(
                        "INSERT INTO bookmarks VALUES (?, ?, ?, ?, ?)",
                        (uuid4().hex, book.id, *entry),
                    )
                    existing.add(entry)
                    added += 1
        return added

    def backup(self, path):
        self.flush_positions()
        destination = sqlite3.connect(path)
        try:
            self.db.backup(destination)
        finally:
            destination.close()
