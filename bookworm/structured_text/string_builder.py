# coding: utf-8

from __future__ import annotations

import attr

from bookworm import typehints as t
from bookworm.utils import NEWLINE


@attr.s(auto_attribs=True, slots=True)
class StringBuilder:
    lines: list[str] = attr.ib(factory=list, init=False)
    data: t.Optional[str] = ""
    newline: str = NEWLINE

    def __attrs_post_init__(self):
        self.lines.append(self.data)

    def getvalue(self):
        return "".join(self.lines)

    def tell(self):
        return sum(len(s) for s in self.lines)

    def get_last_position(self):
        if (pos := self.tell() - 1) >= 0:
            return pos
        return 0

    def write(self, text):
        self.lines.append(text)

    def writeline(self, text, strip_linebreaks=True):
        text = text if not strip_linebreaks else text.strip()
        self.lines.append(text + self.newline)

    @property
    def is_starting_newline(self):
        if (not self.lines) or self.lines[-1].endswith(self.newline):
            return True
        return False

    def ensure_newline(self):
        if not self.is_starting_newline:
            self.writeline(text="")
