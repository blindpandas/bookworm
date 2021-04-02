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


class SemanticElementType(IntEnum):
    HEADING = auto()
    LINK = auto()
    LIST = auto()
    CODE_BLOCK = auto()
    QUOTE = auto()
    TABLE = auto()
    FIGURE = auto()


# Maps semantic element types to (label, should_speak_whole_text)
SEMANTIC_ELEMENT_OUTPUT_OPTIONS = {
    SemanticElementType.HEADING: (_("Heading"), True),
    SemanticElementType.LINK: (_("Link"), True),
    SemanticElementType.LIST: (_("LIST"), False),
    SemanticElementType.CODE_BLOCK: (_("Code Block"), False),
    SemanticElementType.QUOTE: (_("Quote"), False),
    SemanticElementType.TABLE: (_("Table"), False),
    SemanticElementType.FIGURE: (_("Image"), False),
}

@dataclass
class TextStructureMetadata:
    """Provides metadata about a blob of text based on ranges."""
    element_map: dict

    def iter_ranges(self, element_type):
        for rngs in self.element_map.get(element_type, ()):
            yield rngs

    def get_next_element_pos(self, element_type, anchor=0):
        if not (element_ranges := self.element_map.get(element_type, ())):
            return
        for start, stop in element_ranges:
            if start > anchor:
                return start, stop

    def get_prev_element_pos(self, element_type, anchor=0):
        if not (element_ranges := self.element_map.get(element_type, ())):
            return
        element_ranges.reverse()
        for start, stop in element_ranges:
            if (start < anchor) and not (start <= anchor <= stop):
                return start, stop
