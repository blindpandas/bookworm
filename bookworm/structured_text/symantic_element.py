# coding: utf-8

import re
from chemical import it, ChemicalException
from enum import IntEnum, auto
from dataclasses import dataclass, field
from bookworm import typehints as t
from bookworm.utils import normalize_line_breaks
from bookworm.logger import logger


log = logger.getChild(__name__)


class Style(IntEnum):
    NORMAL = auto()
    BOLD = auto()
    ITALIC = auto()
    UNDERLINED = auto()
    STRIKETHROUGH = auto()
    SUPERSCRIPT = auto()
    SUBSCRIPT = auto()
    HIGHLIGHTED = auto()
    MONOSPACED = auto()
    DISPLAY_1 = auto()
    DISPLAY_2 = auto()
    DISPLAY_3 = auto()
    DISPLAY_4 = auto()


class SymanticElementType(IntEnum):
    PARAGRAPH = auto()
    HEADING = auto()
    LIST = auto()
    LIST_ITEM = auto()
    CODE_BLOCK = auto()
    QUOTE = auto()
    TABLE = auto()
    FIGURE = auto()


@dataclass
class TextStructureMetadata:
    """Provides metadata about a blob of text based on ranges."""
    element_map: dict

    def iter_ranges(self, element_type):
        for rngs in self.element_map.get(element_type, ()):
            yield rngs

    def get_next_element_pos(self, element_type, anchor=0):
        element_ranges = self.element_map.get(element_type, ())
        try:
            return it(element_ranges).find(lambda r: r[0] > anchor)
        except ChemicalException:
            return

    def get_prev_element_pos(self, element_type, anchor=0):
        element_ranges = self.element_map.get(element_type, ())
        try:
            return it(element_ranges).map(lambda r: range(*r)).find(lambda r: (anchor not in r) and (r.start < anchor))
        except ChemicalException:
            return

