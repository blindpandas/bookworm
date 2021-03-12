# coding: utf-8

import trafilatura
from io import StringIO
from chemical import it
from lxml import etree
from functools import cached_property
from bookworm.utils import NEWLINE
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

class WebPage(BasePage):
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

    def get_image(self, *args, **kwargs):
        raise NotImplementedError


class WebHtmlDocument(FluidDocument):
    """For html documents."""

    __internal__ = True
    format = "webpage"
    capabilities = DC.TOC_TREE | DC.METADATA | DC.ASYNC_READ

    def __len__(self):
        return len(self._sections)

    def get_page(self, index: int) -> WebPage:
        return WebPage(self, index)

    def get_html(self, url):
        fetched = trafilatura.fetch_url(url)
        return trafilatura.utils.load_html(fetched)

    def read(self):
        super().read()
        self.text_buffer = StringIO()
        self._outline = None
        self._metainfo = None
        self._parse_html(self.get_html(self.uri.path))

    def get_content(self):
        return self.text_buffer.getvalue().strip()

    def close(self):
        super().close()
        if (text_buffer := getattr(self, 'text_buffer', None)) is not None:
            text_buffer.close()

    @cached_property
    def toc_tree(self):
        root = self._outline
        if len(root) == 1:
            return root[0]
        return root

    @cached_property
    def metadata(self):
        return self._metainfo

    def _parse_html(self, html):
        meta_info = trafilatura.metadata.extract_metadata(html) or {}
        doc_title = meta_info.get('title', "")
        if not doc_title:
            doc_title = html.xpath("head/title").text
        self._metainfo = BookMetadata(
            title=doc_title,
            author=meta_info.get('author', ""),
            publisher=meta_info.get('sitename', ""),
            publication_year=meta_info.get('date', ""),
        )
        extracted = trafilatura.extract(html, output_format='xml')
        xml_content = etree.fromstring(extracted)
        main_content = xml_content.xpath("main")[0]
        root = Section(document=self, pager=None, title=doc_title, level=1, position=0)
        stack = TreeStackBuilder(root)
        for node in main_content.iterchildren():
            text = NEWLINE + (node.text or "") + NEWLINE
            if node.tag == 'head':
                section = Section(
                    document=self,
                    pager=None,
                    title=node.text.strip("\n"),
                    level=2,
                    position=self.text_buffer.tell(),
                )
                stack.push(section)
            self.text_buffer.write(text)
        self._sections = list(root.iter_children()) or [
            root,
        ]
        self._outline = root
        root.pager = Pager(first=0, last=len(self._sections))
        for i, sect in enumerate(self._sections):
            sect.pager = Pager(first=i, last=i)
