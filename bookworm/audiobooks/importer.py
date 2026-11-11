"""Read local audio without changing tags or copying users' recordings."""

import hashlib
import math
import os
import re
import stat as stat_module
from collections import Counter
from dataclasses import replace
from pathlib import Path
from threading import Event
from uuid import uuid4

import mutagen

from .model import Audiobook, Chapter

EXTENSIONS = {".mp3", ".m4b", ".m4a", ".wav", ".flac", ".ogg", ".opus"}
MAX_FILES = 20000


class ImportCancelledError(Exception):
    pass


def check_audio_file(path):
    """Fast preflight; complete decoding is a separate cancellable operation."""
    path = Path(path)
    try:
        stat = path.stat()
        if not path.is_file():
            raise ValueError(_("This path is not an audio file: {file}").format(file=path))
        if stat.st_size == 0:
            raise ValueError(_("The audio file is empty (0 bytes): {file}").format(file=path))
        if path.suffix.casefold() not in EXTENSIONS:
            raise ValueError(_("This audio file format is not supported: {file}").format(file=path))
        with path.open("rb") as stream:
            if not stream.read(16):
                raise ValueError(
                    _("The audio file has no readable content: {file}").format(file=path)
                )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            _("The audio file was not found. It may have been moved or deleted: {file}").format(
                file=path
            )
        ) from exc
    except PermissionError as exc:
        raise PermissionError(
            _(
                "Access to this audio file was denied. Check its permissions or whether another program has locked it: {file}"
            ).format(file=path)
        ) from exc
    return stat


def natural_key(value):
    return tuple(
        (1, int(p)) if p.isdigit() else (0, p.casefold()) for p in re.split(r"(\d+)", str(value))
    )


def fingerprint(path, cancel=None):
    """Full-file identity; run off the GUI thread for imports and relocation."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            if cancel is not None and cancel.is_set():
                raise ImportCancelledError
            digest.update(block)
    return digest.hexdigest()


def _tag(tags, *keys):
    for key in keys:
        try:
            value = tags.get(key)
        except ValueError:
            # Vorbis comments reject MP4's non-ASCII tag names. Continue with
            # their own schema instead of rejecting valid FLAC/Ogg/Opus files.
            continue
        if value is not None:
            if hasattr(value, "text"):
                value = value.text
            if isinstance(value, (list, tuple)):
                value = value[0] if value else ""
            if str(value).strip():
                return str(value).strip()
    return ""


def _number(tags, *keys):
    raw = _tag(tags, *keys)
    match = re.search(r"\d+", raw)
    return int(match.group()) if match else 0


def _inspect(path, root, cancel=None):
    check_audio_file(path)
    audio = mutagen.File(path)
    if audio is None or not hasattr(audio.info, "length"):
        raise ValueError(_("Unrecognized audio file: {file}").format(file=path.name))
    length = float(audio.info.length)
    if not math.isfinite(length) or length <= 0:
        raise ValueError(_("Invalid audio duration: {file}").format(file=path.name))
    duration = max(1, round(length * 1000))
    tags = audio.tags or {}
    title = _tag(tags, "TIT2", "\u00a9nam", "title") or path.stem
    album = _tag(tags, "TALB", "\u00a9alb", "album")
    author = _tag(tags, "TPE2", "aART", "albumartist", "TPE1", "\u00a9ART", "artist")
    disc = _number(tags, "TPOS", "disk", "discnumber")
    track = _number(tags, "TRCK", "trkn", "tracknumber")
    points = {}
    for item in getattr(audio, "chapters", None) or ():
        if math.isfinite(item.start) and 0 <= item.start * 1000 < duration:
            points[round(item.start * 1000)] = item.title or title
    if path.suffix.lower() in {".m4b", ".m4a"} and not points:
        from .backend import probe_mp4_chapters

        for start, name in probe_mp4_chapters(path):
            if 0 <= start < duration:
                points[start] = name or title
    if hasattr(tags, "getall"):
        for item in tags.getall("CHAP"):
            if 0 <= item.start_time < duration:
                points[item.start_time] = _tag(item.sub_frames, "TIT2") or title
    # Never discard an introduction before the first embedded chapter.
    points.setdefault(0, title)
    starts = sorted(points)
    relative = path.relative_to(root).as_posix()
    size = path.stat().st_size
    signature = fingerprint(path, cancel)
    mtime = path.stat().st_mtime_ns
    chapters = tuple(
        Chapter(
            relative,
            points[start],
            start,
            starts[i + 1] if i + 1 < len(starts) else duration,
            size,
            signature,
            mtime,
        )
        for i, start in enumerate(starts)
    )
    return disc, track, album, author, chapters


def import_book(source, cancel=None, progress=None, *, verify=False):
    """Import one file or one book folder (including its disc subfolders).

    The caller previews the resulting order before adding the book. A failure
    aborts the whole import: chapters are never silently omitted.
    """
    cancel = cancel or Event()
    source = Path(source).resolve()
    root = source if source.is_dir() else source.parent
    if source.is_dir():
        files = []

        def folder_error(error):
            raise OSError(
                _("The audio folder could not be read completely: {folder}").format(
                    folder=error.filename
                )
            ) from error

        for folder, directories, names in os.walk(source, onerror=folder_error, followlinks=False):
            if cancel.is_set():
                raise ImportCancelledError
            # os.walk(followlinks=False) alone can still traverse Windows
            # directory junctions. Do not scan another book through a reparse
            # point, or recurse through a junction back to an ancestor.
            directories[:] = [
                name
                for name in directories
                if not (Path(folder) / name).is_symlink()
                and not (
                    getattr((Path(folder) / name).lstat(), "st_file_attributes", 0)
                    & getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                )
                and (Path(folder) / name).resolve().is_relative_to(root)
            ]
            for name in names:
                path = Path(folder) / name
                if path.suffix.lower() not in EXTENSIONS or path.is_symlink():
                    continue
                if not path.resolve().is_relative_to(root):
                    continue
                # Do not hide a recording that disappears during the scan: its
                # preflight will produce an actionable error instead.
                files.append(path)
                if len(files) > MAX_FILES:
                    raise ValueError(_("Too many audio files in this folder."))
        files.sort(key=lambda p: natural_key(p.relative_to(root)))
    else:
        check_audio_file(source)
        files = [source]
    if not files:
        raise ValueError(_("No supported audio files were found."))
    inspected = []
    for index, path in enumerate(files):
        if cancel.is_set():
            raise ImportCancelledError
        if progress:
            progress(index + 1, len(files), path.name)
        try:
            inspected.append((path, _inspect(path, root, cancel)))
        except (mutagen.MutagenError, OSError, ValueError) as exc:
            raise ValueError(
                _("Cannot import {file}: {reason}").format(file=path.name, reason=str(exc))
            ) from exc
    # Use tag order only when every file has a unique, complete disc/track pair.
    # Incomplete/duplicated tags must not arbitrarily move tracks to the front.
    pairs = [(info[0], info[1]) for _, info in inspected]
    if all(track > 0 for _, track in pairs) and len(set(pairs)) == len(pairs):
        inspected.sort(key=lambda item: (item[1][0], item[1][1]))
    albums = [info[2] for _, info in inspected if info[2]]
    authors = [info[3] for _, info in inspected if info[3]]
    title = Counter(albums).most_common(1)[0][0] if albums else source.stem
    author = Counter(authors).most_common(1)[0][0] if authors else ""
    chapters = tuple(c for _, info in inspected for c in info[4])
    if cancel.is_set():
        raise ImportCancelledError
    book = Audiobook(uuid4().hex, title, author, str(root), chapters)
    if verify:
        from .exporter import verify_recordings

        try:
            verify_recordings(book, cancel, progress)
        except Exception as exc:
            if cancel.is_set():
                raise ImportCancelledError from exc
            raise
    return book


def relocate_book(book, root, cancel=None):
    cancel = cancel or Event()
    relocated = replace(book, root=str(Path(root).resolve(strict=True)))
    checked = {}
    for index, chapter in enumerate(book.chapters):
        if cancel.is_set():
            raise ImportCancelledError
        if chapter.path in checked:
            continue
        path = relocated.absolute_path(index)
        if path.stat().st_size != chapter.size or fingerprint(path, cancel) != chapter.fingerprint:
            raise ValueError(
                _("This is not the original recording: {file}").format(file=chapter.path)
            )
        checked[chapter.path] = path.stat().st_mtime_ns
    return replace(
        relocated, chapters=tuple(replace(c, mtime_ns=checked[c.path]) for c in relocated.chapters)
    )
