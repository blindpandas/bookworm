# coding: utf-8

import re
from itertools import chain
from lxml import html as html_parser
from inscriptis import Inscriptis
from bookworm import typehints as t
from bookworm.logger import logger
from .symantic_element import (
    Style,
    SymanticElementType,
)


log = logger.getChild(__name__)
RE_STRIP_XML_DECLARATION = re.compile(r'^<\?xml [^>]+?\?>')


SYMANTIC_HTML_ELEMENTS = {
    SymanticElementType.PARAGRAPH: {"p",},
    SymanticElementType.HEADING: {f"h{l}" for l in range(1, 7)},
    SymanticElementType.LIST: {"ol", "ul",},
    SymanticElementType.LIST_ITEM: {"li",},
    SymanticElementType.QUOTE: {"blockquote", "q",},
    SymanticElementType.CODE_BLOCK: {"code",},
    SymanticElementType.TABLE: {"table",},
    SymanticElementType.FIGURE: {"img", "figure", "picture",},
}

STYLE_HTML_ELEMENTS = {
    Style.BOLD: {"b", "strong", "emph", "details", "summary", "dfn",},
    Style.ITALIC: {"i", "small", "ruby", "rb", "rt",},
    Style.UNDERLINED: {"u",},
    Style.STRIKETHROUGH: {"del", "strike", "s"},
    Style.HIGHLIGHTED: {"mark",},
    Style.MONOSPACED: {"output", "samp", "kbd", "var"},
    Style.DISPLAY_1: {"h1", },
    Style.DISPLAY_2: {"h2", "h3", },
    Style.DISPLAY_3: {"h4", "h5", },
    Style.DISPLAY_4: {"h6", },
}
SYMANTIC_TAG_MAP = {t: k for k, v in SYMANTIC_HTML_ELEMENTS.items() for t in v}
STYLE_TAG_MAP = {t: k for k, v in STYLE_HTML_ELEMENTS.items() for t in v}


class StructuredInscriptis(Inscriptis):
    """Subclass of ```inscriptis.Inscriptis``` to record the position of structural elements."""

    def __init__(self, *args, **kwargs):
        self.symantic_elements = {}
        self.styled_elements = {}
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
        text_start_pos = len(self.get_text())
        tag = tree.tag
        if isinstance(tag, str):
            self.handle_starttag(tag, tree.attrib)
            if tree.text:
                self.handle_data(tree.text)

            for node in tree:
                self._parse_html_tree(node)

            self.handle_endtag(tag)

        if tree.tail:
            self.handle_data(tree.tail)
    
        text_end_pos = len(self.get_text())
        if isinstance(tag, str) and (text_start_pos != text_end_pos):
            self.record_tag_info(
                tag,
                text_start_pos,
                text_end_pos
            )

    def record_tag_info(self, tag, start_pos, end_pos):
        if tag in SYMANTIC_TAG_MAP:
            self.symantic_elements.setdefault(SYMANTIC_TAG_MAP[tag], []).append((start_pos, end_pos))
        if tag in STYLE_TAG_MAP:
            self.styled_elements.setdefault(STYLE_TAG_MAP[tag], []).append((start_pos, end_pos))
