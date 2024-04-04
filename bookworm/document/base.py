# coding: utf-8

from __future__ import annotations

import gc
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Sequence
from functools import cached_property, lru_cache, wraps
from pathlib import Path

import pywhatlang
from more_itertools import flatten
from selectolax.parser import HTMLParser

from bookworm import typehints as t
from bookworm.concurrency import QueueProcess, call_threaded
from bookworm.i18n import LocaleInfo
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from bookworm.structured_text import SemanticElementType, Style, TextRange
from bookworm.utils import (
    get_url_spans,
    normalize_line_breaks,
    remove_excess_blank_lines,
)

from . import operations as doctools
from .elements import *
from .exceptions import DocumentIOError, PaginationError, UnsupportedDocumentFormatError
from .features import DocumentCapability, ReadingMode

log = logger.getChild(__name__)
PAGE_CACHE_CAPACITY = 300


class BaseDocument(Sequence, Iterable, metaclass=ABCMeta):
    """Defines the core interface of a document."""

    __internal__ = False
    """A flag to indicate whether this type of document is visible to the user."""

    format: str = None
    """The developer oriented format of this document."""

    name: str = None
    """The displayable name of this document format."""

    extensions: t.Tuple[str] = None
    """The file extension(s) of this format."""

    capabilities: DocumentCapability = DocumentCapability.NULL_CAPABILITY
    """A combination of DocumentCapability flags."""

    supported_reading_modes: t.Tuple[ReadingMode] = (ReadingMode.DEFAULT,)
    default_reading_mode: ReadingMode = ReadingMode.DEFAULT

    document_classes: dict[str, t.ForwardRef("BaseDocument")] = {}
    """A dict of subclasses representing supported document types."""

    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        if (cls.format is not None) and cls.check():
            cls.document_classes[cls.format.lower()] = cls

    @classmethod
    def get_document_class_given_format(cls, format):
        return cls.document_classes.get(format.lower())

    @classmethod
    def get_supported_file_extensions(cls):
        exts = flatten(
            doc_cls.extensions
            for doc_cls in cls.document_classes.values()
            if doc_cls.extensions is not None
        )
        return frozenset(ext.lstrip("*") for ext in exts)

    @classmethod
    def check(cls):
        """Return True if this document format is supported based on the user's environment."""
        return True

    def __init__(self, uri):
        self.uri = uri

    def __contains__(self, value: int):
        return -1 < value < len(self)

    def __getitem__(self, index: int) -> BasePage:
        return self.get_page(index)

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def __getstate__(self) -> dict:
        """Support for pickling."""
        return dict(uri=self.uri)

    def __setstate__(self, state):
        """Support for unpickling."""
        self.__dict__.update(state)
        self.read()

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}: "
            f"format={self.format}, "
            f"capabilities={self.capabilities!r}, "
            f"uri={self.uri!r}"
            ">"
        )

    @cached_property
    def reading_options(self):
        reading_mode = int(
            self.uri.openner_args.get("reading_mode", ReadingMode.DEFAULT)
        )
        return ReadingOptions(
            reading_mode=ReadingMode(reading_mode),
        )

    @cached_property
    def identifier(self) -> str:
        """Return a unique identifier for this document."""
        return self.uri.to_uri_string()

    @abstractmethod
    def read(self):
        """
        Perform the actual IO operations for loading the ebook.
        Subclasses should call super to ensure the standard behavior.
        """

    def close(self):
        """Perform the actual IO operations for unloading the ebook.
        Subclasses should call super to ensure the standard behavior.
        """
        gc.collect()

    @abstractmethod
    def get_page(self, index: int) -> BasePage:
        """Return the page object at index."""

    def get_page_number_from_page_label(self, page_label):
        if DocumentCapability.PAGE_LABELS not in self.capabilities:
            raise NotImplementedError(
                "This feature is not enabled for this class of documents"
            )
        for page in self:
            page_label = page_label.lower()
            if page.get_label().lower() == page_label:
                return page
        raise LookupError(f"Failed to find a page with the label {page_label}.")

    @property
    @abstractmethod
    def toc_tree(self) -> t.Iterable[Section]:
        """Return an iterable representing the table of content.
        The items should be of type `Section`.
        """

    @cached_property
    def language(self) -> str:
        num_pages = len(self)
        num_samples = num_pages if num_pages <= 20 else 20
        text = "".join(self[i].get_text() for i in range(num_samples))
        return self.get_language(samples=text, is_html=False)

    @property
    @abstractmethod
    def metadata(self) -> BookMetadata:
        """Return a `BookMetadata` object holding info about this book."""

    @lru_cache(maxsize=1000)
    def get_page_content(self, page_number: int) -> str:
        """Convenience method: return the text content of a page."""
        return self[page_number].get_text()

    def get_page_image(self, page_number: int, zoom_factor: float = 1.0) -> ImageIO:
        """Convenience method: return the image of a page."""
        return self[page_number].get_image(zoom_factor)

    def get_cover_image(self) -> t.Optional[ImageIO]:
        """Return the cover image of this document."""

    def get_file_system_path(self):
        """Only valid for documents that have true filesystem path."""
        if (filepath := Path(self.uri.path)).exists():
            return filepath
        raise DocumentIOError(f"File {filepath} does not exist.")

    @classmethod
    def should_read_async(cls):
        return DocumentCapability.ASYNC_READ in cls.capabilities

    @classmethod
    def uses_chapter_by_chapter_navigation_model(self):
        return self.default_reading_mode is ReadingMode.CHAPTER_BASED

    @classmethod
    def supports_structural_navigation(cls):
        return DocumentCapability.STRUCTURED_NAVIGATION in cls.capabilities

    @classmethod
    def supports_links(cls):
        return (
            DocumentCapability.LINKS in cls.capabilities
            or DocumentCapability.INTERNAL_ANCHORS in cls.capabilities
        )

    @classmethod
    def is_single_page_document(cls):
        return DocumentCapability.SINGLE_PAGE in cls.capabilities

    @classmethod
    def has_toc_tree(self):
        return DocumentCapability.TOC_TREE in self.capabilities

    @classmethod
    def can_render_pages(self):
        return DocumentCapability.GRAPHICAL_RENDERING in self.capabilities

    @staticmethod
    def get_language(samples, is_html=False, hint_language: str = "en") -> LocaleInfo:
        """Return the language of this document.
        By default we use a heuristic based on whatlang.
        """
        if is_html:
            samples = HTMLParser(samples).text()
        try:
            lang_code, confidence, is_reliable = pywhatlang.detect_lang(samples)
        except:
            log.error(f"Failed to recognize document language", exc_info=True)
        else:
            return LocaleInfo(lang_code).parent
        return LocaleInfo(hint_language)

    def export_to_text(self, target_filename: t.PathLike):
        return QueueProcess(
            target=doctools.export_to_plain_text,
            args=(self, target_filename),
            name="document-export",
        )

    def search(self, request: doctools.SearchRequest):
        yield from QueueProcess(
            target=doctools.search_book, args=(self, request), name="document-search"
        )


class BasePage(metaclass=ABCMeta):
    """Represents a page from the document."""

    __slots__ = ["document", "index"]

    def __init__(self, document: BaseDocument, index: int):
        self.document = document
        self.index = index

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.index}>"

    @abstractmethod
    def get_text(self) -> str:
        """Return the text content or raise NotImplementedError."""

    def get_image(self, zoom_factor: float) -> ImageIO:
        """
        Return page image as `ImageIO`
        or raise NotImplementedError.
        """
        raise NotImplementedError

    def get_label(self) -> str:
        """Return the page label string (commonly found on PDFs)."""
        return ""

    def get_semantic_structure(
        self,
    ) -> dict[SemanticElementType, list[tuple[int, int]]]:
        """Return information about the position of semantic elements."""
        raise NotImplementedError

    def get_style_info(self) -> dict[SemanticElementType, list[tuple[int, int]]]:
        """Return information about the position of styled elements."""
        raise NotImplementedError

    def resolve_link(self, link_range) -> LinkTarget:
        raise NotImplementedError

    def get_link_for_text_range(self, text_range) -> LinkTarget:
        retval = self.get_external_link_target(text_range)
        if retval is None:
            try:
                retval = self.resolve_link(text_range)
            except NotImplementedError:
                retval = None
        return retval

    @property
    def semantic_structure(self):
        try:
            semantic_structure = self.get_semantic_structure()
        except NotImplementedError:
            semantic_structure = {}
        semantic_link_ranges = semantic_structure.setdefault(
            SemanticElementType.LINK, []
        )
        all_link_ranges = [
            *semantic_link_ranges,
            *(
                text_range
                for (text_range, __url) in self.get_external_links()
                if text_range not in semantic_link_ranges
            ),
        ]
        semantic_structure[SemanticElementType.LINK] = all_link_ranges
        return semantic_structure

    def get_external_links(self) -> tuple[tuple[int, int], str]:
        return get_url_spans(self.get_text())

    def get_external_link_target(self, text_range) -> str:
        if url := dict(self.get_external_links()).get(text_range):
            return LinkTarget(url=url, is_external=True)

    def normalize_text(self, text):
        return remove_excess_blank_lines(text)

    @property
    def number(self) -> int:
        """The user facing page number."""
        return self.index + 1

    @cached_property
    def section(self) -> Section:
        """The (most specific) section that this page blongs to."""
        rv = self.document.toc_tree
        for sect in rv.iter_children():
            if self.index in sect.pager:
                rv = sect
                if sect.pager.first > self.index:
                    break
        return rv

    @property
    def is_first_of_section(self) -> bool:
        return self.index == self.section.pager.first

    @property
    def is_last_of_section(self) -> bool:
        return self.index == self.section.pager.last

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.document is other.document) and (self.index == other.index)
        return NotImplemented


class SinglePage(BasePage):
    """Emulates a page for a single page document."""

    def get_text(self):
        return self.document.get_content()

    def get_semantic_structure(self):
        return self.document.get_document_semantic_structure()

    def get_table_markup(self, table_index):
        return self.document.get_document_table_markup(table_index)

    def get_style_info(self):
        return self.document.get_document_style_info()

    def resolve_link(self, link_range):
        return self.document.resolve_link(link_range)


class SinglePageDocument(BaseDocument):
    """Provides sain defaults for single page documents."""

    def __len__(self):
        return 1

    @abstractmethod
    def get_content(self) -> str:
        """Get the content of this document."""

    def get_page(self, index: int) -> SinglePage:
        return SinglePage(self, index)

    @cached_property
    def language(self) -> str:
        return self.get_language(samples=self.get_content()[:2000], is_html=False)

    def get_section_at_position(self, pos):
        """Return the section at the given position."""
        rv = self.toc_tree
        for sect in rv.iter_children():
            if pos in sect.text_range:
                rv = sect
                if sect.text_range.start > pos:
                    break
        return rv

    def get_document_semantic_structure(self):
        raise NotImplementedError

    def get_document_style_info(self):
        raise NotImplementedError

    def get_document_table_markup(self, table_index):
        raise NotImplementedError

    def resolve_link(self, text_range):
        raise NotImplementedError

    def search(self, request: doctools.SearchRequest):
        text = self.get_content()[request.text_range.as_slice()]
        yield from QueueProcess(
            target=doctools.search_single_page_document,
            args=(
                text,
                request,
            ),
            name="document-search",
        )


class DummyDocument(BaseDocument):
    """Implements core document methods for a dummy document."""

    __indexable__ = True

    def __len__(self):
        raise NotImplementedError

    def get_page(self, index):
        raise NotImplementedError

    @property
    def toc_tree(self):
        raise NotImplementedError

    @property
    def metadata(self):
        raise NotImplementedError


class VirtualDocument:
    """
    A Marker to denote a virtual document.
    Subclasses of this should be considered one shot documents.
    """

    def __init__(self):
        self.uri.view_args.update(
            {
                "is_virtual": True,
                "save_last_position": False,
                "add_to_recents": False,
                "allow_pinning": False,
            }
        )

    def search(self, request: doctools.SearchRequest):
        yield from doctools.search_book(self, request)

    def export_to_text(self, target_filename: t.PathLike):
        yield from doctools.export_to_plain_text(self, target_filename)
