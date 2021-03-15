# coding: utf-8

import trafilatura
import requests
from io import StringIO
from pycld2 import detect as detect_language, error as CLD2Error
from diskcache import Cache
from chemical import it
from lxml import etree
from functools import cached_property
from bookworm.paths import home_data_path
from bookworm.http_tools import HttpResource
from bookworm.utils import NEWLINE
from bookworm.document_formats.base import (
    BasePage,
    FluidDocument,
    Section,
    Pager,
    BookMetadata,
    DocumentCapability as DC,
    DocumentError,
    DocumentIOError,
    ChangeDocument,
    TreeStackBuilder,
)
from bookworm.document_formats.html_document import HtmlPage
from bookworm.logger import logger


log = logger.getChild(__name__)
EXPIRE_TIMEOUT = 60 * 60 * 24 * 2


class WebHtmlDocument(FluidDocument):
    """For Openning html documents from URLS."""

    __internal__ = True
    format = "webpage"
    capabilities = DC.TOC_TREE | DC.METADATA | DC.ASYNC_READ

    def __len__(self):
        return len(self._sections)

    def get_page(self, index: int):
        return HtmlPage(self, index)

    def _get_cache_directory(self):
        return str(home_data_path("_web_cache"))

    def get_html(self, url):
        _cache = Cache(self._get_cache_directory(), eviction_policy='least-frequently-used')
        try:
            req = HttpResource(url).download()
            if 'html' not in req.content_type.lower():
                raise DocumentError("Not HTML content ")
        except ConnectionError as e:
            log.exception(f"Failed to obtain resource from url: {url}", exc_info=True)
            req = None
        stored_content, tag = _cache.get(url, tag=True)
        if (stored_content is not None):
            if (req is None) or (tag == req.etag):
                return stored_content
        html_string = req.get_text()
        _cache.set(url, html_string, tag=req.etag, expire=EXPIRE_TIMEOUT)
        return html_string

    @cached_property
    def language(self):
        try:
            (success, _, ((_, lang, _, _), *_)) = detect_language(
                utf8Bytes=self.html_string, isPlainText=False, hintLanguage=None
            )
        except CLD2Error as e:
            log.error(f"Failed to recognize document language", exc_info=True)
            success = False
        if success:
            return lang
        return "en"

    def read(self):
        super().read()
        self.text_buffer = StringIO()
        self._outline = None
        self._metainfo = None
        try:
            self.html_string = self.get_html(self.uri.path)
            html_elm = trafilatura.utils.load_html(self.html_string)
        except Exception as e:
            log.exception("Failed to retrieve html content.", exc_info=True)
            raise DocumentIOError("Failed to retrieve data") from e
        self._parse_html(html_elm)

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
