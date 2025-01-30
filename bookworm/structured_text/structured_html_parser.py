# coding: utf-8

from __future__ import annotations

import re
from functools import cached_property
from itertools import chain

import ftfy
from inscriptis import Inscriptis
from inscriptis.css_profiles import RELAXED_CSS_PROFILE, STRICT_CSS_PROFILE
from inscriptis.model.config import ParserConfig
from lxml import html as html_parser
from selectolax.parser import HTMLParser

from bookworm import typehints as t
from bookworm.logger import logger
from bookworm.structured_text import SemanticElementType, Style
from bookworm.utils import remove_excess_blank_lines

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
        "_table_elements",
    ]

    @staticmethod
    def normalize_html(html_string):
        config = ftfy.TextFixerConfig(
            fix_character_width=False,
            uncurl_quotes=False,
            fix_latin_ligatures=False,
            normalization='NFC',
            unescape_html=False,
            fix_line_breaks=True,
            max_decode_length=MAX_DECODE_LENGTH
        )
        html_string = ftfy.fix_text(html_string, config)
        return remove_excess_blank_lines(html_string)

    def __init__(self, *args, **kwargs):
        self.link_range_to_target = {}
        self.anchors = {}
        self.html_id_ranges = {}
        self.styled_elements = {}
        self._table_elements = []
        kwargs.setdefault("config", INSCRIPTIS_CONFIG)
        super().__init__(*args, **kwargs)

    def _parse_html_tree(self, state, tree):
        canvas = state.canvas
        try:
            start_index = canvas.current_block.idx
        except TypeError:
            start_index = 0
        super()._parse_html_tree(state, tree)
        end_index = canvas.current_block.idx
        try:
            anot = canvas.annotations[-1]
        except IndexError:
            pass
        else:
            if tree.tag == "a" and (href := tree.attrib.get("href", "")):
                self.link_range_to_target[(anot.start, anot.end)] = href
        if (anch := tree.attrib.get("id", "")) or (anch := tree.attrib.get("name", "")):
            element_range = (start_index, end_index)
            self.anchors[anch] = element_range
            self.html_id_ranges[anch] = element_range
        if tree.tag == "table":
            self._table_elements.append(tree)

        return state.canvas

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

    def get_table_markup(self, table_index):
        parsed = HTMLParser(
            html_parser.tostring(self._table_elements[table_index], encoding="unicode")
        )
        parsed.unwrap_tags(
            [
                "a",
            ]
        )
        return parsed.html
