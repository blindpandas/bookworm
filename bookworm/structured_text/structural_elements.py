# coding: utf-8

"""Provides elements that help to define the structure for a blob of text."""

import re
from itertools import chain
from chemical import it, ChemicalException
from enum import IntEnum, auto
from dataclasses import dataclass, field
from bookworm import typehints as t
from bookworm.utils import normalize_line_breaks
from .primitives import TextRange


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
    HEADING_1 = auto()
    HEADING_2 = auto()
    HEADING_3 = auto()
    HEADING_4 = auto()
    HEADING_5 = auto()
    HEADING_6 = auto()
    ANCHOR = auto()
    LINK = auto()
    LIST = auto()
    QUOTE = auto()
    TABLE = auto()
    FIGURE = auto()


HEADING_LEVELS = {
    SemanticElementType.HEADING_1,
    SemanticElementType.HEADING_2,
    SemanticElementType.HEADING_3,
    SemanticElementType.HEADING_4,
    SemanticElementType.HEADING_5,
    SemanticElementType.HEADING_6,
}
# Maps semantic element types to (label, should_speak_whole_text)
SEMANTIC_ELEMENT_OUTPUT_OPTIONS = {
    SemanticElementType.HEADING: (_("Heading"), True),
    SemanticElementType.HEADING_1: (_("Heading level 1"), True),
    SemanticElementType.HEADING_2: (_("Heading level 2"), True),
    SemanticElementType.HEADING_3: (_("Heading level 3"), True),
    SemanticElementType.HEADING_4: (_("Heading level 4"), True),
    SemanticElementType.HEADING_5: (_("Heading level 5"), True),
    SemanticElementType.HEADING_6: (_("Heading level 6"), True),
    SemanticElementType.ANCHOR: (_("Anchor"), True),
    SemanticElementType.LINK: (_("Link"), True),
    SemanticElementType.LIST: (_("LIST"), False),
    SemanticElementType.QUOTE: (_("Quote"), True),
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

    def get_range(self, element_ranges, forward, anchor):
        element_ranges.sort()
        if not forward:
            element_ranges.reverse()
        for start, stop in element_ranges:
            condition = (
                start > anchor
                if forward
                else (start < anchor) and not (start <= anchor <= stop)
            )
            if condition:
                return start, stop

    def get_element(self, element_type, forward, anchor):
        if element_type is SemanticElementType.HEADING:
            heading_map = {
                h: self.element_map[h] for h in HEADING_LEVELS if h in self.element_map
            }
            ranges = (
                (h, self.get_range(rng, forward, anchor))
                for h, rng in heading_map.items()
            )
            filtered_ranges = filter(lambda r: r[1] is not None, ranges)
            sorted_ranges = tuple(
                sorted(
                    filtered_ranges,
                    key=lambda x: x[1][0],
                    reverse=not forward,
                )
            )
            if sorted_ranges:
                element_type, pos = sorted_ranges[0]
                return pos, element_type
        if (element_ranges := self.element_map.get(element_type, ())) :
            if (pos := self.get_range(element_ranges, forward, anchor)) :
                return pos, element_type

    def get_next_element_pos(self, element_type, anchor):
        return self.get_element(element_type, True, anchor)

    def get_prev_element_pos(self, element_type, anchor):
        return self.get_element(element_type, False, anchor)
