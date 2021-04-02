# coding: utf-8

import re
from itertools import chain
from lxml import html as html_parser
from inscriptis import Inscriptis
from inscriptis.model.config import ParserConfig
from bookworm import typehints as t
from bookworm.utils import remove_excess_blank_lines
from bookworm.logger import logger
from .structure import (
    Style,
    SemanticElementType,
)


log = logger.getChild(__name__)
RE_STRIP_XML_DECLARATION = re.compile(r'^<\?xml [^>]+?\?>')
InscriptisConfig = ParserConfig(
    display_images=True,
)

SEMANTIC_HTML_ELEMENTS = {
    SemanticElementType.HEADING: {f"h{l}" for l in range(1, 7)},
    SemanticElementType.LIST: {"ol", "ul",},
    # SemanticElementType.LINK: {"a",},
    SemanticElementType.QUOTE: {"blockquote", "q",},
    SemanticElementType.CODE_BLOCK: {"code",},
    SemanticElementType.TABLE: {"table",},
}

STYLE_HTML_ELEMENTS = {
    Style.BOLD: {"b", "strong", "emph",},
    Style.ITALIC: {"i", "small",},
    Style.UNDERLINED: {"u",},
    Style.STRIKETHROUGH: {"del", "strike", "s"},
    Style.HIGHLIGHTED: {"mark",},
    #Style.MONOSPACED: {"output", "samp", "kbd", "var"},
    # Style.SUPERSCRIPT: {"sup",},
    # Style.SUBSCRIPT: {"sub",},
    Style.DISPLAY_1: {"h1", },
    Style.DISPLAY_2: {"h2", "h3",},
    Style.DISPLAY_3: {"h4", "h5",},
    Style.DISPLAY_4: {"h6", },
}
SEMANTIC_TAG_MAP = {t: k for k, v in SEMANTIC_HTML_ELEMENTS.items() for t in v}
STYLE_TAG_MAP = {t: k for k, v in STYLE_HTML_ELEMENTS.items() for t in v}



class StructuredInscriptis(Inscriptis):
    """Subclass of ```inscriptis.Inscriptis``` to record the position of structural elements."""
    TAGS_OF_INTEREST = set(SEMANTIC_TAG_MAP).union(STYLE_TAG_MAP)

    def __init__(self, *args, **kwargs):
        self.semantic_elements = {}
        self.styled_elements = {}
        kwargs.setdefault("config", InscriptisConfig)
        super().__init__(*args, **kwargs)

    @classmethod
    def from_string(cls, html_string):
        html_content = html_string.strip()
        if not html_content:
            return ''
        # strip XML declaration, if necessary
        if html_content.startswith('<?xml '):
            html_content = RE_STRIP_XML_DECLARATION.sub('', html_content, count=1)
        return cls(html_parser.fromstring(html_content))

    def _parse_html_tree(self, tree):
        if (tag := tree.tag) not in self.TAGS_OF_INTEREST:
            return super()._parse_html_tree(tree)
        text_start_pos = len(self.get_text())
        super()._parse_html_tree(tree)
        text_end_pos = len(self.get_text())
        if text_start_pos != text_end_pos:
            self.record_tag_info(
                tag,
                text_start_pos,
                text_end_pos
            )

    def get_text(self):
        text = super().get_text()
        return remove_excess_blank_lines(text)

    def record_tag_info(self, tag, start_pos, end_pos):
        if tag in SEMANTIC_TAG_MAP:
            self.semantic_elements.setdefault(SEMANTIC_TAG_MAP[tag], []).append((start_pos, end_pos))
        if tag in STYLE_TAG_MAP:
            self.styled_elements.setdefault(STYLE_TAG_MAP[tag], []).append((start_pos, end_pos))
