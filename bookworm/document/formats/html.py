# coding: utf-8

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from urllib import parse as urllib_parse
from urllib.request import url2pathname

import requests
from lxml import etree
from lxml import html as lxml_html
from more_itertools import first as get_first_element
from more_itertools import zip_offset
from yarl import URL

from bookworm.http_tools import HttpResource
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from bookworm.structured_text import (
    HEADING_LEVELS,
    SemanticElementType,
    Style,
    TextRange,
)
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
from bookworm.utils import (
    NEWLINE,
    TextContentDecoder,
    escape_html,
    is_external_url,
    remove_excess_blank_lines,
)

from .. import SINGLE_PAGE_DOCUMENT_PAGER, BookMetadata, ChangeDocument
from .. import DocumentCapability as DC
from .. import (
    DocumentError,
    DocumentIOError,
    LinkTarget,
    ReadingMode,
    Section,
    SinglePageDocument,
    TreeStackBuilder,
)

log = logger.getChild(__name__)
# Default cache timeout
EXPIRE_TIMEOUT = 7 * 24 * 60 * 60


def get_clean_html(html_string: str) -> (str, BookMetadata):
    """Clean the given html using trafilatura."""

    # trafilatura has a memory leak issue
    # Therefore, we run it in a separate process

    import trafilatura
    from trafilatura.external import JT_STOPLIST, custom_justext

    html_string = StructuredHtmlParser.normalize_html(html_string)

    # Extract metadata
    meta_info = trafilatura.metadata.extract_metadata(html_string)
    doc_title = meta_info.title
    if not doc_title:
        html = lxml_html.fromstring(html_string)
        extracted_title = html.xpath("/html/head/title//text()")
        # Certain pages seem to return a list instead of a string
        # It may have to do with invalid bytes
        # An example: https://bw.enabc.net/doc/
        if isinstance(extracted_title, list) and extracted_title:
            extracted_title = extracted_title[0]
        doc_title = extracted_title if extracted_title else ""
    doc_metadata = BookMetadata(
        title=doc_title,
        author=meta_info.author or "",
        publisher=meta_info.sitename or "",
        publication_year=meta_info.date or "",
    )

    # Extract the body
    extracted = trafilatura.extract(
        html_string, output_format="xml", include_links=True
    )
    xml_content = etree.fromstring(extracted)
    main_content = xml_content.xpath("main")[0]
    for node in main_content.cssselect("head"):
        node.tag = "h2"
    output_template = [
        "<html><body>",
        "<h1>%s</h1>" % (escape_html(doc_metadata.title),),
        lxml_html.tostring(
            main_content, pretty_print=False, method="html", encoding="unicode"
        ),
        "</body></html>",
    ]
    return ("".join(output_template), doc_metadata)


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
        reading_mode = self.reading_options.reading_mode
        if reading_mode == reading_mode.CLEAN_VIEW:
            self.parse_to_clean_text()
        elif reading_mode == ReadingMode.FULL_TEXT_VIEW:
            self.parse_to_full_text()
        else:
            self.parse_html()

    def parse_html(self):
        return self.parse_to_full_text()

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
        if root.title is None:
            root.title = self.metadata.title
        return root

    @cached_property
    def metadata(self):
        return self._metainfo

    def resolve_link(self, link_range) -> LinkTarget:
        href = self.link_targets[link_range]
        if is_external_url(href):
            return LinkTarget(url=href, is_external=True)
        else:
            _filename, anchor = href.split("#") if "#" in href else (href, None)
            if anchor := self.anchors.get(anchor, None):
                return LinkTarget(url=href, is_external=False, position=anchor)

    def parse_to_clean_text(self):
        with ProcessPoolExecutor(max_workers=1) as executor:
            task = executor.submit(get_clean_html, self.html_string)
            try:
                result = task.result()
            except Exception as e:
                log.exception(
                    "Failed to parse html string for clean view", exc_info=True
                )
                raise DocumentIOError from e
            html_content, metadata = result
            self._metainfo = metadata
            return self.parse_text_and_structure(html_content)

    def parse_to_full_text(self):
        html = lxml_html.fromstring(self.html_string)
        # Extract metadata
        title_els = html.cssselect("title")
        title = _("HTML Document") if not title_els else title_els[0].text
        author_el = html.cssselect('head > meta[name="author"]')
        author = "" if not author_el else author_el[0].get("content")
        self._metainfo = BookMetadata(title=title, author=author)
        return self.parse_text_and_structure(self.html_string)

    def parse_text_and_structure(self, html):
        if type(html) in (str, bytes):
            extracted_text_and_info = StructuredHtmlParser.from_string(html)
        else:
            extracted_text_and_info = StructuredHtmlParser(html)
        self.structure = extracted_text_and_info
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
            for (start_pos, stop_pos), h_element in heading_poses:
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
            for this_sect, next_sect in zip_offset(
                all_sections, all_sections, offsets=(0, 1)
            ):
                this_sect.text_range.stop = next_sect.text_range.start - 1
            last_pos = len(text)
            if all_sections:
                all_sections[-1].text_range.stop = last_pos
            root.text_range = TextRange(0, last_pos)

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

    def get_document_table_markup(self, table_index):
        return self.structure.get_table_markup(table_index)

    def get_document_embedded_image_info(self, image_index):
        return self.structure.get_image_info(image_index)

    def get_document_embedded_image(self, image_index) -> ImageIO:
        image_info = self.get_document_embedded_image_info(image_index)
        if image_info.src.lower().startswith("data:image/"):
            try:
                return ImageIO.from_data_uri(image_info.src)
            except Exception as e:
                raise DocumentIOError("Failed to decode embedded image") from e
        if not self._is_local_image_source(image_info.src):
            raise DocumentIOError("Remote images are not supported")
        image_path = self._resolve_image_path(image_info.src)
        if image := ImageIO.from_filename(image_path, preserve_mode=True):
            return image
        raise DocumentIOError(f"Failed to load embedded image: {image_path}")

    @staticmethod
    def _is_local_image_source(src: str) -> bool:
        parsed = urllib_parse.urlparse(src)
        scheme = parsed.scheme.lower()
        if scheme == "":
            return not parsed.netloc
        return scheme == "file" or (len(scheme) == 1 and scheme.isalpha())

    def _resolve_image_path(self, src: str) -> Path:
        if src.lower().startswith("file:"):
            return self._file_uri_to_path(src)
        clean_src = src.split("#", 1)[0].split("?", 1)[0]
        image_path = Path(urllib_parse.unquote(clean_src))
        if image_path.is_absolute():
            return image_path
        if self._image_base_url:
            resolved_src = urllib_parse.urljoin(self._image_base_url, src)
            if not self._is_local_image_source(resolved_src):
                raise DocumentIOError("Remote images are not supported")
            return self._local_image_source_to_path(resolved_src)
        base_path = getattr(self, "filename", None) or self.get_file_system_path()
        return Path(base_path).parent / image_path

    @staticmethod
    def _file_uri_to_path(src: str) -> Path:
        parsed = urllib_parse.urlparse(src)
        path = f"//{parsed.netloc}{parsed.path}" if parsed.netloc else parsed.path
        return Path(url2pathname(path))

    @classmethod
    def _local_image_source_to_path(cls, src: str) -> Path:
        if src.lower().startswith("file:"):
            return cls._file_uri_to_path(src)
        clean_src = src.split("#", 1)[0].split("?", 1)[0]
        return Path(urllib_parse.unquote(clean_src))

    @cached_property
    def _image_base_url(self) -> str:
        try:
            html = lxml_html.fromstring(self.html_string)
        except Exception:
            return ""
        base_href = get_first_element(html.xpath("//base[@href]/@href"), "").strip()
        if not base_href:
            return ""
        base_path = getattr(self, "filename", None) or self.get_file_system_path()
        document_base_url = Path(base_path).parent.resolve().as_uri()
        if not document_base_url.endswith("/"):
            document_base_url += "/"
        return urllib_parse.urljoin(document_base_url, base_href)


class FileSystemHtmlDocument(BaseHtmlDocument):
    format = "html"
    # Translators: the name of a document file format
    name = _("HTML Document")
    extensions = ("*.html", "*.htm", "*.xhtml")

    def get_html(self):
        content = TextContentDecoder.from_filename(self.filename).get_utf8()
        return StructuredHtmlParser.preprocess_html_string(content)

    def read(self):
        self.filename = self.get_file_system_path()
        super().read()

    def parse_html(self):
        return self.parse_to_full_text()


class WebHtmlDocument(BaseHtmlDocument):
    __internal__ = True
    format = "webpage"
    supported_reading_modes = (
        ReadingMode.DEFAULT,
        ReadingMode.CLEAN_VIEW,
        ReadingMode.FULL_TEXT_VIEW,
    )

    def get_html(self):
        if (html_string := getattr(self, "html_string", None)) is not None:
            return html_string
        url = self.uri.path
        try:
            req = HttpResource(url).download()
        except ConnectionError as e:
            log.exception(f"Failed to obtain resource from url: {url}", exc_info=True)
            req = None
            raise DocumentIOError from e
        html_string = StructuredHtmlParser.preprocess_html_string(req.get_text())
        html_tree = lxml_html.fromstring(html_string)
        html_tree.make_links_absolute(
            base_url=url, resolve_base_href=True, handle_failures="discard"
        )
        current_url_path = URL(url).path
        # Now strip the base_url from internal anchors
        for maybe_internal_anchor in html_tree.xpath(
            f"//a[starts-with(@href, '{url}')]"
        ):
            href = maybe_internal_anchor.get("href")
            if (URL(href).path) != current_url_path:
                continue
            if "#" in href:
                maybe_internal_anchor.set("href", "#" + href.split("#")[1])
        return lxml_html.tostring(html_tree, encoding="unicode")

    def parse_html(self):
        return self.parse_to_clean_text()
