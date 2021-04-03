# coding: utf-8

import trafilatura
import requests
from io import StringIO
from pathlib import Path
from contextlib import contextmanager
from functools import cached_property
from chemical import it
from diskcache import Cache
from lxml import etree
from trafilatura.external import custom_justext, JT_STOPLIST
from bookworm.paths import home_data_path
from bookworm.http_tools import HttpResource
from bookworm.document_formats.base import (
    SinglePageDocument,
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
from bookworm.structured_text import (
    StructuredInscriptis,
    SemanticElementType,
    Style,
    HEADING_LEVELS
)
from bookworm.logger import logger


log = logger.getChild(__name__)
# Default cache timeout
EXPIRE_TIMEOUT  = 7 * 24 * 60 * 60


class BaseHtmlDocument(SinglePageDocument):
    """For html documents."""

    capabilities = DC.TOC_TREE | DC.METADATA | DC.STRUCTURED_NAVIGATION | DC.TEXT_STYLE

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

    def read(self):
        super().read()
        self.text_buffer = StringIO()
        self._text = None
        self._outline = None
        self._metainfo = None
        self._semantic_structure = {}
        self._style_info = {}
        try:
            self.html_string = self.get_html()
        except Exception as e:
            log.exception("Failed to retrieve html content.", exc_info=True)
            raise DocumentIOError("Failed to get html") from e
        html = trafilatura.utils.load_html(self.html_string)
        self.parse_metadata(html)
        reading_mode = self.reading_options.reading_mode
        if reading_mode == reading_mode.CLEAN_VIEW:
            self.parse_to_clean_text(html)
        elif reading_mode == ReadingMode.FULL_TEXT_VIEW:
            self.parse_to_full_text(html)
        else:
            self.parse_html(html)

    def get_content(self):
        return self._text

    def get_document_semantic_structure(self):
        return self._semantic_structure

    def get_document_style_info(self):
        return self._style_info

    def close(self):
        super().close()
        if (text_buffer := getattr(self, "text_buffer", None)) is not None:
            text_buffer.close()

    @cached_property
    def language(self):
        return self.get_language(self.html_string, is_html=True)

    @cached_property
    def toc_tree(self):
        root = self._outline
        if len(root) == 1:
            return root[0]
        return root

    @cached_property
    def metadata(self):
        return self._metainfo

    def _get_heading_level(self, parag):
        return int(parag.dom_path[-1])

    @contextmanager
    def _create_toc_stack(self):
        root = Section(
            document=self, pager=None, title=self._metainfo.title, level=1, position=0
        )
        stack = TreeStackBuilder(root)
        yield stack
        self._sections = list(root.iter_children()) or [
            root,
        ]
        self._outline = root
        root.pager = Pager(first=0, last=len(self._sections))
        for i, sect in enumerate(self._sections):
            sect.pager = Pager(first=i, last=i)

    def parse_metadata(self, html):
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

    def parse_to_full_text(self, html):
        extracted_text_and_info = StructuredInscriptis(html)
        self._semantic_structure = extracted_text_and_info.semantic_elements
        self._style_info = extracted_text_and_info.styled_elements
        self._text = text = extracted_text_and_info.get_text()
        start_poses = sorted((
                (rng, h)
                for h, rngs in extracted_text_and_info.semantic_elements.items()
                for rng in rngs
                if h in HEADING_LEVELS
            ),
            key=lambda x: x[0]
        )
        with self._create_toc_stack() as stack:
            for ((start_pos, stop_pos), h_element) in start_poses:
                h_text = text[start_pos:stop_pos].strip()
                h_level = int(h_element.name[-1])
                section = Section(
                    document=self,
                    pager=None,
                    title=h_text,
                    level=h_level,
                    position=start_pos,
                )
                stack.push(section)

    def parse_to_clean_text(self, html):
        extracted = trafilatura.extract(html, output_format="xml")
        xml_content = etree.fromstring(extracted)
        main_content = xml_content.xpath("main")[0]
        with self._create_toc_stack() as stack:
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
