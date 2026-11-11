"""A book has an ordered timeline, irrespective of physical file boundaries."""

import re
from bisect import bisect_right
from dataclasses import asdict, dataclass
from functools import cached_property
from pathlib import Path, PurePosixPath, PureWindowsPath


@dataclass(frozen=True)
class Chapter:
    path: str
    title: str
    start_ms: int
    end_ms: int
    size: int
    fingerprint: str
    mtime_ns: int = 0

    def __post_init__(self):
        # Stored paths always use '/' and must be relative on every platform.
        # WindowsPath('/name').is_absolute() is False (no drive), even though
        # joining it replaces the root directory. Parse the portable syntax.
        path = PurePosixPath(self.path)
        if (
            path.is_absolute()
            or PureWindowsPath(self.path).drive
            or ".." in path.parts
            or "\\" in self.path
        ):
            raise ValueError("Chapter paths must be relative to the book folder")
        if not 0 <= self.start_ms < self.end_ms or self.size <= 0:
            raise ValueError("Invalid chapter duration or size")

    @property
    def duration_ms(self):
        return self.end_ms - self.start_ms


@dataclass(frozen=True)
class Audiobook:
    id: str
    title: str
    author: str
    root: str
    chapters: tuple[Chapter, ...]

    def __post_init__(self):
        if not self.id or not self.title.strip() or not self.chapters:
            raise ValueError("An audiobook must have a title and chapters")

    @cached_property
    def offsets(self):
        result = [0]
        for chapter in self.chapters:
            result.append(result[-1] + chapter.duration_ms)
        return tuple(result)

    @property
    def duration_ms(self):
        return self.offsets[-1]

    def locate(self, position_ms):
        position_ms = max(0, min(int(position_ms), self.duration_ms))
        index = min(bisect_right(self.offsets, position_ms) - 1, len(self.chapters) - 1)
        return index, self.chapters[index].start_ms + position_ms - self.offsets[index]

    def absolute_path(self, index):
        root = Path(self.root).resolve()
        path = (root / self.chapters[index].path).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Audio file is outside the book folder")
        return path

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        return cls(**{**value, "chapters": tuple(Chapter(**c) for c in value["chapters"])})


def format_time(milliseconds, include_milliseconds=False):
    seconds = max(0, int(milliseconds)) // 1000
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    result = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return result + f".{max(0, int(milliseconds)) % 1000:03d}" if include_milliseconds else result


def parse_time(value):
    """Accept seconds, mm:ss or hh:mm:ss; reject negative or ambiguous values."""
    parts = value.strip().replace(",", ".").split(":")
    if (
        not 1 <= len(parts) <= 3
        or not all(re.fullmatch(r"[0-9]+", p) for p in parts[:-1])
        or not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,3})?", parts[-1])
    ):
        raise ValueError(
            _("Use seconds, mm:ss or hh:mm:ss, optionally with up to three decimal places.")
        )
    whole, _separator, fraction = parts[-1].partition(".")
    numbers = [int(p) for p in parts[:-1]] + [int(whole)]
    if len(numbers) > 1 and any(n >= 60 for n in numbers[1:]):
        raise ValueError(_("Minutes and seconds after a colon must be below 60."))
    total = 0
    for number in numbers:
        total = total * 60 + number
    return total * 1000 + int(fraction.ljust(3, "0"))
