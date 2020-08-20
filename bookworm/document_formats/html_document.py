# coding: utf-8

from pathlib import Path
from io import StringIO
from chemical import it
from selectolax.parser import HTMLParser
from itertools import chain
from bookworm.utils import cached_property, NEWLINE
from bookworm.document_formats.base import (
    BasePage,
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
BLOCK_TAGS = {"p", "br", "div", "ul", "ol", "li", "table", "td", "tr"}
IGNORED_TAGS = {
    "script",
    "style",
}


class HtmlPage(BasePage):
    """Emulates a page for a fluid document."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections = self.document._sections

    def get_text(self):
        section = self.sections[self.index]
        start_pos = section.position
        end_pos = (
            self.sections[self.index + 1].position
            if (self.index + 1) < len(self.sections)
            else -1
        )
        self.document.text_buffer.seek(start_pos)
        if end_pos == -1:
            text = self.document.text_buffer.read()
        else:
            text = self.document.text_buffer.read(end_pos - start_pos)
        return "\n".join(it(text.split("\n")).filter(lambda line: line.strip()))

    def get_image(self, zoom_factor=1.0, enhance=False):
        raise NotImplementedError


class HtmlDocument(FluidDocument):
    """For html documents."""

    format = "html"
    # Translators: the name of a document file format
    name = _("Web page")
    extensions = ("*.html", "*.htm", "*.xhtml")
    capabilities = DC.TOC_TREE | DC.METADATA | DC.ASYNC_READ

    def __len__(self):
        return len(self._sections)

    def get_page(self, index: int) -> HtmlPage:
        return HtmlPage(self, index)

    def _get_document_content(self):
        with open(self.filename, "r", encoding="utf8") as file:
            return file.read()

    def read(self):
        super().read()
        self.text_buffer = StringIO()
        self._outline = None
        self._metainfo = None
        self._parse_html(self._get_document_content())

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
                author=el_author.attrs.get("content", "")
                if el_author is not None
                else "",
            )
        root = Section(document=self, pager=None, title=title, level=1, position=0)
        stack = TreeStackBuilder(root)
        for node in html.body.traverse():
            if node.tag in IGNORED_TAGS:
                continue
            node_text = node.text(deep=False)
            if node.tag in HEADING_TAGS:
                section = Section(
                    document=self,
                    pager=None,
                    title=node.text().strip("\n"),
                    level=int(node.tag[1]),
                    position=self.text_buffer.tell(),
                )
                stack.push(section)
                text = NEWLINE + node_text + NEWLINE
            elif node.tag in BLOCK_TAGS:
                text = node_text + NEWLINE
            else:
                text = node_text + " "
            self.text_buffer.write(text)
        self._sections = list(root.iter_children())
        self._outline = root
        root.pager = Pager(first=0, last=len(self._sections))
        for i, sect in enumerate(self._sections):
            sect.pager = Pager(first=i, last=i)
