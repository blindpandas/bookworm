"""Caching utilities"""

from pathlib import Path

from diskcache import Cache


def is_document_modified(key: str, path: Path, cache: Cache) -> bool:
    """
    Checks whether a particular document was modified
    We can currently afford to naively just stat() the file_path in order to determine it
    """
    mtime = cache.get(f"{key}_meta")
    if not mtime:
        # No information for the book was found, so return True just to be safe
        # TODO: Is this acceptable?
        return True
    stat_mtime = path.stat().st_mtime
    return mtime != stat_mtime


def set_document_modified_time(key: str, path: Path, cache: Cache) -> bool:
    key = f"{key}_meta"
    cache.set(key, path.stat().st_mtime)
