# coding: utf-8

from __future__ import annotations
import trafilatura
import requests
from pathlib import Path
from contextlib import contextmanager
from functools import cached_property
from more_itertools import zip_offset
from chemical import it
from diskcache import Cache
from lxml import etree
from lxml.html import etree as HtmlEtree
from trafilatura.external import custom_justext, JT_STOPLIST
from bookworm.paths import home_data_path
from bookworm.http_tools import HttpResource
from bookworm.structured_text import (
    TextRange,
    SemanticElementType,
    Style,
    HEADING_LEVELS,
)
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
from bookworm.utils import remove_excess_blank_lines, escape_html, is_external_url, NEWLINE
from bookworm.logger import logger
from .. import (
    SinglePageDocument,
    Section,
    LinkTarget,
    SINGLE_PAGE_DOCUMENT_PAGER,
    BookMetadata,
    DocumentCapability as DC,
    ReadingMode,
    DocumentError,
    DocumentIOError,
    ChangeDocument,
    TreeStackBuilder,
)


log = logger.getChild(__name__)
# Default cache timeout
EXPIRE_TIMEOUT = 7 * 24 * 60 * 60


class BaseHtmlDocument(SinglePageDocument):
    """For html documents."""

    capabilities = (
        DC.TOC_TREE
        | DC.METADATA
        | DC.SINGLE_PAGE
        | DC.STRUCTURED_NAVIGATION
        | DC.TEXT_STYLE
        | DC.ASYNC_READ
        | DC.LINKS
        | DC.INTERNAL_ANCHORS
    )

    supported_reading_modes = (
        ReadingMode.DEFAULT,
        ReadingMode.CLEAN_VIEW,
        ReadingMode.FULL_TEXT_VIEW,
    )

    def __getstate__(self) -> dict:
        """Support for pickling."""
        return super().__getstate__() | dict(html_string=self.html_string)

    def read(self):
        super().read()
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

    def resolve_link(self, link_range) -> LinkTarget:
        href = self.link_targets[link_range]
        if is_external_url(href):
            return LinkTarget(url=href, is_external=True)
        else:
            _filename, anchor = (
                href.split("#")
                if "#" in href
                else (href, None)
            )
            if (anchor_range := self.anchors.get(anchor , None)):
                return LinkTarget(
                    url=href,
                    is_external=False,
                    position=anchor_range[0]
                )

    def _get_heading_level(self, parag):
        return int(parag.dom_path[-1])

    @contextmanager
    def _create_toc_stack(self):
        root = Section(
            pager=SINGLE_PAGE_DOCUMENT_PAGER,
            text_range=TextRange(0, -1),
            title=self._metainfo.title,
            level=1,
        )
        stack = TreeStackBuilder(root)
        yield stack, root
        self._outline = root

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

    def parse_text_and_structure(self, html):
        extracted_text_and_info = StructuredHtmlParser(html)
        self._semantic_structure = extracted_text_and_info.semantic_elements
        self._style_info = extracted_text_and_info.styled_elements
        self.link_targets = extracted_text_and_info.link_targets
        self.anchors = extracted_text_and_info.anchors
        self._text = text = extracted_text_and_info.get_text()
        heading_poses = sorted(
            (
                (rng, h)
                for h, rngs in extracted_text_and_info.semantic_elements.items()
                for rng in rngs
                if h in HEADING_LEVELS
            ),
            key=lambda x: x[0],
        )
        with self._create_toc_stack() as (stack, root):
            for ((start_pos, stop_pos), h_element) in heading_poses:
                h_text = text[start_pos:stop_pos].strip()
                h_level = int(h_element.name[-1])
                section = Section(
                    pager=SINGLE_PAGE_DOCUMENT_PAGER,
                    title=h_text,
                    level=h_level,
                    text_range=TextRange(start_pos, stop_pos),
                )
                stack.push(section)
            all_sections = tuple(root.iter_children())
            for (this_sect, next_sect) in zip_offset(
                all_sections, all_sections, offsets=(0, 1)
            ):
                this_sect.text_range.stop = next_sect.text_range.start - 1
            last_pos = len(text)
            if all_sections:
                all_sections[-1].text_range.stop = last_pos
            root.text_range = TextRange(0, last_pos)

    def parse_to_full_text(self, html):
        return self.parse_text_and_structure(html)

    def parse_to_clean_text(self, html):
        extracted = trafilatura.extract(html, output_format="xml")
        xml_content = etree.fromstring(extracted)
        main_content = xml_content.xpath("main")[0]
        for node in main_content.cssselect("head"):
            node.tag = "h2"
        html_string = (
            "<html><body>"
            + f"<h1>{escape_html(self.metadata.title)}</h1>"
            + HtmlEtree.tostring(
                main_content,
                encoding="unicode",
                pretty_print=False,
                method="html",
            )
            + "</body></html>"
        )
        return self.parse_text_and_structure(HtmlEtree.fromstring(html_string))


class FileSystemHtmlDocument(BaseHtmlDocument):

    format = "html"
    # Translators: the name of a document file format
    name = _("HTML Document")
    extensions = ("*.html", "*.htm", "*.xhtml")

    def get_html(self):
        with open(self.filename, "r", encoding="utf8") as file:
            return StructuredHtmlParser.normalize_html(file.read())

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
