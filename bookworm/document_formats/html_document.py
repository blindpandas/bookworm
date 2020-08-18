# coding: utf-8

from pathlib import Path
from io import StringIO
from selectolax.parser import HTMLParser
from bookworm.utils import cached_property, NEWLINE
from bookworm.document_formats.base import (
    FluidDocument,
    Section,
    Pager,
    BookMetadata,
    DocumentCapability as DC,
    DocumentError,
    TreeStackBuilder,
)
from bookworm.logger import logger


log = logger.getChild(__name__)

HEADING_TAGS = {f"{h}{level}" for level in range(1, 7) for h in ("h", "H")}
BLOCK_TAGS = {"p", "br", "div", "ul", "ol", "li", "table"}
IGNORED_TAGS = {"script", "style",}


class HtmlDocument(FluidDocument):
    """For html documents."""

    format = "html"
    # Translators: the name of a document file format
    name = _("Web page")
    extensions = ("*.html", "*.htm", "*.xhtml")
    capabilities = DC.FLUID_PAGINATION|DC.TOC_TREE|DC.METADATA|DC.ASYNC_READ

    def _get_document_content(self):
        with open(self.filename, "r", encoding="utf8") as file:
            return file.read()

    def read(self):
        self.text_buffer = StringIO()
        self._outline = None
        self._metainfo = None
        self._parse_html(self._get_document_content())
        super().read()

    def get_content(self):
        return self.text_buffer.getvalue().strip()

    def close(self):
        super().close()

    @cached_property
    def toc_tree(self):
        root = self._outline
        if len(root) == 1:
            return root[0]
        return root

    @cached_property
    def metadata(self):
        return self._metainfo

    def _parse_html(self, html_string):
        html = HTMLParser(html_string)
        head = html.css_first("head")
        title = Path(self.filename).stem
        if head is not None:
            title = head.css_first("title").text()
            el_author = head.css_first('meta[name="author"]')
            self._metainfo = BookMetadata(
                title=title,
                author=el_author.attrs.get("content", "") if el_author is not None else ""
            )
        pager = Pager(first=0, last=0)
        root = Section(document=self, pager=pager, title=title, level=1, data={"position": 0})
        stack = TreeStackBuilder(root)
        for node in html.body.iter():
            if node.tag in IGNORED_TAGS:
                continue
            node_text = node.text().strip("\n")
            if node.tag in HEADING_TAGS:
                section = Section(
                    document=self,
                    pager=pager,
                    title=node.text().strip("\n"),
                    level=int(node.tag[1]),
                    data={"position": self.text_buffer.tell() + 1}
                )
                stack.push(section)
                self.text_buffer.write(NEWLINE + node_text + NEWLINE)
            elif node.tag in BLOCK_TAGS:
                self.text_buffer.write(node_text + NEWLINE)
            else:
                self.text_buffer.write(node_text)
        self._outline = root

