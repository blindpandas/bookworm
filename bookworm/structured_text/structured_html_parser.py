# coding: utf-8

from __future__ import annotations
import re
import ftfy
from functools import cached_property
from itertools import chain
from uritools import isuri
from lxml import html as html_parser
from selectolax.parser import HTMLParser
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
INSCRIPTIS_PARSE_HTML_TREE = Inscriptis._parse_html_tree
INSCRIPTIS_GET_TEXT = Inscriptis.get_text
MAX_DECODE_LENGTH = int(5e6)
RE_STRIP_XML_DECLARATION = re.compile(r"^<\?xml [^>]+?\?>")
TAGS_TO_STRIP = [
    "form",
    "input",
    "button",
    "select",
    "fieldset",
    "legend",
    "strong",
    "small",
    "link",
    "span",
    "emph",
    "b",
    "i",
    "img",
    "sub",
    "sup",
]
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

    @staticmethod
    def normalize_html(html_string):
        html_string = ftfy.fix_text(
            html_string,
            normalization="NFKC",
            fix_entities=False,
            fix_line_breaks=True,
            max_decode_length=MAX_DECODE_LENGTH,
        )
        if len(html_string) > 10000:
            parsed = HTMLParser(html_string)
            parsed.unwrap_tags(TAGS_TO_STRIP)
            html_string = parsed.html
        return html_string

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
        html_content = cls.normalize_html(html_content)
        return cls(html_parser.fromstring(html_content))

    def get_text(self):
        return remove_excess_blank_lines(INSCRIPTIS_GET_TEXT(self))

    def _parse_html_tree(self, tree):
        if (tag := tree.tag) not in self.tags_of_interest:
            return INSCRIPTIS_PARSE_HTML_TREE(self, tree)
        start_pos = len(self.get_text())
        INSCRIPTIS_PARSE_HTML_TREE(self, tree)
        stop_pos = len(self.get_text())
        if start_pos != stop_pos:
            if (element_type := self.SEMANTIC_TAG_MAP.get(tag)) :
                self.semantic_elements.setdefault(element_type, []).append(
                    (start_pos, stop_pos)
                )
