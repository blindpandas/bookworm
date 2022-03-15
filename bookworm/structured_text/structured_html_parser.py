# coding: utf-8

from __future__ import annotations
import re
import ftfy
from functools import cached_property
from itertools import chain
from lxml import html as html_parser
from selectolax.parser import HTMLParser
from inscriptis import Inscriptis
from inscriptis.model.config import ParserConfig
from inscriptis.css_profiles import RELAXED_CSS_PROFILE, STRICT_CSS_PROFILE
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
SEMANTIC_HTML_ELEMENTS = {
    SemanticElementType.HEADING_1: {
        "h1",
        "#aria-role=heading",
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
    SemanticElementType.LINK: {
        "a#href",
        "a#name",
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
    # SemanticElementType.FIGURE: {
    # "img",
    # "figure",
    # "picture",
    # }
}
STYLE_HTML_ELEMENTS = {}
INSCRIPTIS_ANNOTATION_RULES = {
    t: (k,) for (k, v) in SEMANTIC_HTML_ELEMENTS.items() for t in v
}
INSCRIPTIS_CONFIG = ParserConfig(
    css=STRICT_CSS_PROFILE,
    display_images=False,
    deduplicate_captions=True,
    display_links=False,
    annotation_rules=INSCRIPTIS_ANNOTATION_RULES,
)


class StructuredHtmlParser(Inscriptis):
    """Subclass of ```inscriptis.Inscriptis``` to provide the position of structural elements."""

    __slots__ = [
        "link_range_to_target",
        "anchors",
        "styled_elements",
    ]

    @staticmethod
    def normalize_html(html_string):
        html_string = ftfy.fix_text(
            html_string,
            normalization="NFKC",
            unescape_html=False,
            fix_line_breaks=True,
            max_decode_length=MAX_DECODE_LENGTH,
        )
        if len(html_string) > 10000:
            parsed = HTMLParser(html_string)
            # parsed.unwrap_tags(TAGS_TO_STRIP)
            html_string = parsed.html
        return remove_excess_blank_lines(html_string)

    def __init__(self, *args, **kwargs):
        self.link_range_to_target = {}
        self.anchors = {}
        self.html_id_ranges = {}
        self.styled_elements = {}
        kwargs.setdefault("config", INSCRIPTIS_CONFIG)
        super().__init__(*args, **kwargs)

    def _parse_html_tree(self, tree):
        try:
            start_index = self.canvas.current_block.idx
        except TypeError:
            start_index = 0
        super()._parse_html_tree(tree)
        end_index = self.canvas.current_block.idx
        try:
            anot = self.canvas.annotations[-1]
        except IndexError:
            pass
        else:
            if tree.tag == "a" and (href := tree.attrib.get("href", "")):
                self.link_range_to_target[(anot.start, anot.end)] = href
        if (anch := tree.attrib.get("id", "")) or (anch := tree.attrib.get("name", "")):
            element_range = (start_index, end_index)
            self.anchors[anch] = element_range
            self.html_id_ranges[anch] = element_range

    @classmethod
    def preprocess_html_string(cls, html_string):
        html_content = html_string.strip()
        if not html_content:
            raise ValueError("Invalid html content")
        # strip XML declaration, if necessary
        if html_content.startswith("<?xml "):
            html_content = RE_STRIP_XML_DECLARATION.sub("", html_content, count=1)
        html_content = cls.normalize_html(html_content)
        return html_content

    @classmethod
    def from_string(cls, html_string):
        html_content = cls.preprocess_html_string(html_string)
        return cls(html_parser.fromstring(html_content))

    @classmethod
    def from_lxml_html_tree(cls, lxml_html_tree):
        return cls(lxml_html_tree)

    def get_text(self):
        return remove_excess_blank_lines(INSCRIPTIS_GET_TEXT(self))

    @cached_property
    def semantic_elements(self):
        annotations = {}
        for anot in self.get_annotations():
            annotations.setdefault(anot.metadata, []).append((anot.start, anot.end))
        return annotations

    @cached_property
    def link_targets(self):
        return self.link_range_to_target
