# coding: utf-8

from __future__ import annotations
import re
from functools import cached_property
from itertools import chain
from uritools import isuri
from lxml import html as html_parser
from inscriptis import Inscriptis
from inscriptis.model.config import ParserConfig
from bookworm import typehints as t
from bookworm.utils import remove_excess_blank_lines
from bookworm.logger import logger
from bookworm.structured_text import (
    Style,
    SemanticElementType,
)


log = logger.getChild(__name__)
RE_STRIP_XML_DECLARATION = re.compile(r"^<\?xml [^>]+?\?>")
InscriptisConfig = ParserConfig(
    display_images=True,
)

SEMANTIC_HTML_ELEMENTS = {
    SemanticElementType.HEADING_1: {
        "h1",
    },
    SemanticElementType.HEADING_2: {
        "h2",
    },
    SemanticElementType.HEADING_3: {
        "h3",
    },
    SemanticElementType.HEADING_4: {
        "h4",
    },
    SemanticElementType.HEADING_5: {
        "h5",
    },
    SemanticElementType.HEADING_6: {
        "h6",
    },
    SemanticElementType.LIST: {
        "ol",
        "ul",
    },
    SemanticElementType.QUOTE: {
        "blockquote",
        "q",
    },
    SemanticElementType.TABLE: {
        "table",
    },
}
STYLE_HTML_ELEMENTS = {}


class StructuredHtmlParser(Inscriptis):
    """Subclass of ```inscriptis.Inscriptis``` to record the position of structural elements."""

    SEMANTIC_TAG_MAP = {t: k for k, v in SEMANTIC_HTML_ELEMENTS.items() for t in v}
    STYLE_TAG_MAP = {t: k for k, v in STYLE_HTML_ELEMENTS.items() for t in v}

    def __init__(self, *args, **kwargs):
        self.semantic_elements = {}
        self.styled_elements = {}
        self.__link_info = []
        kwargs.setdefault("config", InscriptisConfig)
        super().__init__(*args, **kwargs)

    @cached_property
    def tags_of_interest(self):
        return set(self.SEMANTIC_TAG_MAP).union(self.STYLE_TAG_MAP)

    @classmethod
    def from_string(cls, html_string):
        html_content = html_string.strip()
        if not html_content:
            raise ValueError("Invalid html content")
        # strip XML declaration, if necessary
        if html_content.startswith("<?xml "):
            html_content = RE_STRIP_XML_DECLARATION.sub("", html_content, count=1)
        return cls(html_parser.fromstring(html_content))

    def _parse_html_tree(self, tree):
        if (tag := tree.tag) not in self.tags_of_interest:
            return super()._parse_html_tree(tree)
        text_start_pos = len(self.get_text())
        super()._parse_html_tree(tree)
        text_end_pos = len(self.get_text())
        if text_start_pos != text_end_pos:
            self.record_tag_info(tag, text_start_pos, text_end_pos)

    def get_text(self):
        text = super().get_text()
        return remove_excess_blank_lines(text)

    def record_tag_info(self, tag, start_pos, end_pos):
        if (element_type := self.SEMANTIC_TAG_MAP.get(tag)) :
            self.semantic_elements.setdefault(element_type, []).append(
                (start_pos, end_pos)
            )
        if (element_type := self.STYLE_TAG_MAP.get(tag)) :
            self.styled_elements.setdefault(element_type, []).append(
                (start_pos, end_pos)
            )
