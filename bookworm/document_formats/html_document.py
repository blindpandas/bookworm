# coding: utf-8

import trafilatura
import requests
from io import StringIO
from pathlib import Path
from functools import cached_property
from chemical import it
from pycld2 import detect as detect_language, error as CLD2Error
from diskcache import Cache
from lxml import etree
from selectolax.parser import HTMLParser
from bookworm.paths import home_data_path
from bookworm.http_tools import HttpResource
from bookworm.document_formats.base import (
    BasePage,
    FluidDocument,
    Section,
    Pager,
    BookMetadata,
    DocumentCapability as DC,
    ReadingMode,
    DocumentError,
    DocumentIOError,
    ChangeDocument,
    TreeStackBuilder,
)
from bookworm.utils import NEWLINE
from bookworm.logger import logger


log = logger.getChild(__name__)
EXPIRE_TIMEOUT = 60 * 60 * 24 * 2
HEADING_TAGS = {f"h{level}" for level in range(1, 7)}
BLOCK_TAGS = {
    "p",
    "br",
    "hr",
    "section",
    "code",
    "nav",
    "main",
    "aside",
    "footer",
    "article",
    "table",
    "ol",
    "ul",
    "thead",
    "tbody",
    "dl",
}
DECORATIVE_TAGS = [
    "span",
    "a",
    "div",
    "strong",
    "b",
    "i",
    "pre",
    "em",
    "dd",
    "dt",
    "cite",
    "col",
    "colgroup",
]
IGNORED_TAGS = [
    "script",
    "style",
    "img",
    "_comment",
    "iframe",
    "button",
    "input",
    "form",
]


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

    def get_image(self, zoom_factor=1.0):
        raise NotImplementedError


class BaseHtmlDocument(FluidDocument):
    """For html documents."""

    capabilities = DC.TOC_TREE | DC.METADATA
    supported_reading_modes = (
        ReadingMode.DEFAULT,
        ReadingMode.CLEAN_VIEW,
        ReadingMode.FULL_TEXT_VIEW,
    )

    def __len__(self):
        return len(self._sections)

    def __getstate__(self) -> dict:
        """Support for pickling."""
        return super().__getstate__() | dict(html_string=self.html_string)

    def get_page(self, index: int) -> HtmlPage:
        return HtmlPage(self, index)

    def read(self):
        super().read()
        self.text_buffer = StringIO()
        self._outline = None
        self._metainfo = None
        try:
            self.html_string = self.get_html()
        except Exception as e:
            log.exception("Failed to retrieve html content.", exc_info=True)
            raise DocumentIOError("Failed to get html") from e
        reading_mode = self.reading_options.reading_mode
        if reading_mode == reading_mode.CLEAN_VIEW:
            self.parse_to_clean_text(self.html_string)
        elif reading_mode == ReadingMode.FULL_TEXT_VIEW:
            self.parse_to_full_text(self.html_string)
        else:
            self.parse_html(self.html_string)

    def get_content(self):
        return self.text_buffer.getvalue().strip()

    def close(self):
        super().close()
        if (text_buffer := getattr(self, "text_buffer", None)) is not None:
            text_buffer.close()

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

    @cached_property
    def toc_tree(self):
        root = self._outline
        if len(root) == 1:
            return root[0]
        return root

    @cached_property
    def metadata(self):
        return self._metainfo

    def parse_to_full_text(self, html_string):
        html = HTMLParser(html_string)
        head = html.css_first("head")
        title = Path(self.uri.path).stem
        if head is not None:
            title = head.css_first("title").text()
            el_author = head.css_first('meta[name="author"]')
            self._metainfo = BookMetadata(
                title=title,
                author=el_author.attrs.get("content", "")
                if el_author is not None
                else "",
            )
        html.body.strip_tags(IGNORED_TAGS)
        html.body.unwrap_tags(DECORATIVE_TAGS)
        root = Section(document=self, pager=None, title=title, level=1, position=0)
        stack = TreeStackBuilder(root)
        for node in html.body.iter():
            node_text = node.text(deep=True)
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
        self._sections = list(root.iter_children()) or [
            root,
        ]
        self._outline = root
        root.pager = Pager(first=0, last=len(self._sections))
        for i, sect in enumerate(self._sections):
            sect.pager = Pager(first=i, last=i)

    def parse_to_clean_text(self, html_string):
        html = trafilatura.utils.load_html(html_string)
        meta_info = trafilatura.metadata.extract_metadata(html) or {}
        doc_title = meta_info.get("title", "")
        if not doc_title:
            doc_title = html.xpath("head/title").text
        self._metainfo = BookMetadata(
            title=doc_title,
            author=meta_info.get("author", ""),
            publisher=meta_info.get("sitename", ""),
            publication_year=meta_info.get("date", ""),
        )
        extracted = trafilatura.extract(html, output_format="xml")
        xml_content = etree.fromstring(extracted)
        main_content = xml_content.xpath("main")[0]
        root = Section(document=self, pager=None, title=doc_title, level=1, position=0)
        stack = TreeStackBuilder(root)
        for node in main_content.iterchildren():
            text = NEWLINE + (node.text or "") + NEWLINE
            if node.tag == "head":
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


class FileSystemHtmlDocument(BaseHtmlDocument):

    format = "html"
    # Translators: the name of a document file format
    name = _("HTML Document")
    extensions = ("*.html", "*.htm", "*.xhtml")

    def get_html(self):
        with open(self.filename, "r", encoding="utf8") as file:
            return file.read()

    def read(self):
        self.filename = self.get_file_system_path()
        super().read()

    def parse_html(self, html_string):
        return self.parse_to_full_text(html_string)


class WebHtmlDocument(BaseHtmlDocument):

    __internal__ = True
    format = "webpage"
    capabilities = BaseHtmlDocument.capabilities | DC.ASYNC_READ

    def _get_cache_directory(self):
        return str(home_data_path("_web_cache"))

    def get_html(self):
        if (html_string := getattr(self, "html_string", None)) is not None:
            return html_string
        url = self.uri.path
        _cache = Cache(
            self._get_cache_directory(), eviction_policy="least-frequently-used"
        )
        try:
            req = HttpResource(url).download()
            if "html" not in req.content_type.lower():
                raise DocumentError("Not HTML content ")
        except ConnectionError as e:
            log.exception(f"Failed to obtain resource from url: {url}", exc_info=True)
            req = None
        stored_content, tag = _cache.get(url, tag=True)
        if stored_content is not None:
            if (req is None) or (tag == req.etag):
                return stored_content
        html_string = req.get_text()
        _cache.set(url, html_string, tag=req.etag, expire=EXPIRE_TIMEOUT)
        return html_string

    def parse_html(self, html_string):
        return self.parse_to_clean_text(html_string)
