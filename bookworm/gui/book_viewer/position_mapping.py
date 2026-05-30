"""Position mapping between Bookworm text offsets and wx text control offsets."""

from __future__ import annotations

import re
from bisect import bisect_left
from dataclasses import dataclass, field

TEXT_CTRL_LEADING_OFFSET = 1
RE_NON_BMP_CHAR = re.compile(r"[\U00010000-\U0010ffff]")


@dataclass(frozen=True, slots=True)
class TextCtrlPositionMap:
    """Maps Bookworm text offsets to wx/RichEdit native offsets.

    Bookworm indexes Python strings by code point. RichEdit caret and styling APIs
    count non-BMP characters as two UTF-16 code units and the displayed control
    value also contains a leading sentinel newline. The sentinel line maps to
    clean position -1; document text positions start at 0.
    """

    text: str
    non_bmp_positions: tuple[int, ...] = field(init=False, repr=False)
    non_bmp_native_positions: tuple[int, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        non_bmp_positions = tuple(match.start() for match in RE_NON_BMP_CHAR.finditer(self.text))
        object.__setattr__(self, "non_bmp_positions", non_bmp_positions)
        object.__setattr__(
            self,
            "non_bmp_native_positions",
            tuple(position + offset for offset, position in enumerate(non_bmp_positions)),
        )

    @property
    def last_position(self) -> int:
        return len(self.text)

    def to_text_ctrl_value(self) -> str:
        # RichEdit counts non-BMP chars as two native positions and otherwise truncates
        # the same number of trailing code points from text assigned through wx.
        padding = "\n" * len(self.non_bmp_positions)
        prefix = "\n" * TEXT_CTRL_LEADING_OFFSET
        return f"{prefix}{self.text}\n{padding}"

    def view_to_control_position(self, pos: int) -> int:
        if pos < 0:
            return 0
        clean_pos = max(0, min(pos, len(self.text)))
        extra_native_units = bisect_left(self.non_bmp_positions, clean_pos)
        return clean_pos + extra_native_units + TEXT_CTRL_LEADING_OFFSET

    def control_to_view_position(self, pos: int) -> int:
        if pos < TEXT_CTRL_LEADING_OFFSET:
            return pos - TEXT_CTRL_LEADING_OFFSET
        native_pos = pos - TEXT_CTRL_LEADING_OFFSET
        clean_pos = native_pos - bisect_left(self.non_bmp_native_positions, native_pos)
        return max(0, min(clean_pos, len(self.text)))

    def get_text_by_range(self, start: int, end: int) -> str:
        start = max(0, start)
        if end < 0:
            return self.text[start:]
        return self.text[start : min(end, len(self.text))]
