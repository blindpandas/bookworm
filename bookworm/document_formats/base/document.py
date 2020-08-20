# coding: utf-8

import gc
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from enum import IntFlag, auto
from functools import wraps
from lru import LRU
from pycld2 import detect as detect_language, error as CLD2Error
from bookworm import typehints as t
from bookworm.concurrency import QueueProcess, call_threaded
from bookworm.utils import cached_property, generate_sha1hash_async
from bookworm.logger import logger
from .elements import *
from . import tools as doctools


log = logger.getChild(__name__)
PAGE_CACHE_CAPACITY = 300


class DocumentError(Exception):
    """The base class of all document related exceptions."""


class PaginationError(DocumentError, IndexError):
    """Raised when the  `next` or `prev` page is not available."""


class DocumentCapability(IntFlag):
    """Represents feature flags for a document."""

    NULL_CAPABILITY = auto()
    """Placeholder for abstract classes."""
    ASYNC_READ = auto()
    """Does this document needs to be opened asynchronously."""
    TOC_TREE = auto()
    """Does this document provide a table-of-content?"""
    METADATA = auto()
    """Does this document provide metadata about its author and pub date?"""
    GRAPHICAL_RENDERING = auto()
    """Does this document provide graphical rendition of its pages?"""
    FLUID_PAGINATION = auto()
    """Does this document supports the notion of pages?"""
    IMAGE_EXTRACTION = auto()
    """Does this document supports extracting images out of pages?"""


class BaseDocument(Sequence, metaclass=ABCMeta):
    """Defines the core interface of a document."""

    format: str = None
    """The developer oriented format of this document."""

    name: str = None
    """The displayable name of this document format."""

    extensions: tuple = None
    """The file extension(s) of this format."""

    capabilities: DocumentCapability = DocumentCapability.NULL_CAPABILITY
    """A combination of DocumentCapability flags."""

    def __init__(self, filename: t.PathLike):
        self.filename = filename

    def __contains__(self, value: int):
        return -1 < value < len(self)

    def __getitem__(self, index: int) -> "BasePage":
        if index not in self:
            raise PaginationError(f"Page {index} is out of range.")
        if index in self._page_cache:
            return self._page_cache[index]
        page = self.get_page(index)
        self._page_cache[index] = page
        return page

    def __getstate__(self) -> dict:
        """Support for pickling."""
        return dict(filename=self.filename)

    def __setstate__(self, state):
        """Support for unpickling."""
        self.__dict__.update(state)
        self.read()

    @cached_property
    def identifier(self) -> str:
        """Return a unique identifier for this document.
        By default it returns a `sha1` digest based on
        the document content.
        """
        if type(self._sha1hash) is not str:
            self._sha1hash = self._sha1hash.result()
        return self._sha1hash

    @abstractmethod
    def read(self):
        """Perform the actual IO operations for loading the ebook.
        The base class implementation also start a background thread
        to generate a `sha1` hash based on the content of the file.
        Subclasses should call super to ensure the standard behavior.
        """
        self._page_cache = LRU(PAGE_CACHE_CAPACITY)
        self._page_content_cache = LRU(PAGE_CACHE_CAPACITY)
        self._sha1hash = generate_sha1hash_async(self.filename)
        # XXX Is this a pre-mature optimization?
        call_threaded(lambda: self.language)

    @abstractmethod
    def close(self):
        """Perform the actual IO operations for unloading the ebook.
        Subclasses should call super to ensure the standard behavior.
        """
        self._page_cache.clear()
        self._page_content_cache.clear()
        gc.collect()

    @abstractmethod
    def get_page(self, index: int) -> "BasePage":
        """Return the page object at index."""

    def is_encrypted(self) -> bool:
        """Does this document need password."""
        return False

    def decrypt(self, password):
        """Decrypt this document using the provided password."""
        pass

    @property
    @abstractmethod
    def toc_tree(self) -> t.Iterable[Section]:
        """Return an iterable representing the table of content.
        The items should be of type `Section`.
        """

    @cached_property
    def language(self) -> str:
        """Return the language of this document.
        By default we use a heuristic based on Google's CLD2.
        """
        num_pages = len(self)
        num_samples = num_pages if num_pages <= 20 else 20
        text = "".join(self[i].get_text() for i in range(num_samples)).encode("utf8")
        try:
            (success, _, ((_, lang, _, _), *_)) = detect_language(
                utf8Bytes=text, isPlainText=True, hintLanguage=None
            )
        except CLD2Error as e:
            log.error(f"Failed to recognize document language: {e.args}")
            success = False
        if success:
            return lang
        return "en"

    @property
    @abstractmethod
    def metadata(self) -> BookMetadata:
        """Return a `BookMetadata` object holding info about this book."""

    def get_page_content(self, page_number: int) -> str:
        """Convenience method: return the text content of a page."""
        _cached = self._page_content_cache.get(page_number)
        if _cached is not None:
            return _cached
        content = self[page_number].get_text()
        self._page_content_cache[page_number] = content
        return content

    def get_page_image(
        self, page_number: int, zoom_factor: float = 1.0, enhance: bool = False
    ) -> bytes:
        """Convenience method: return the image of a page."""
        return self[page_number].get_image(zoom_factor, enhance)

    @property
    def supports_async_read(self):
        return DocumentCapability.ASYNC_READ in self.capabilities

    @property
    def is_fluid(self):
        return DocumentCapability.FLUID_PAGINATION in self.capabilities

    @property
    def has_toc_tree(self):
        return DocumentCapability.TOC_TREE in self.capabilities

    def export_to_text(self, target_filename: t.PathLike):
        yield from QueueProcess(
            target=doctools.export_to_plain_text,
            args=(self, target_filename),
            name="bookworm-exporter",
        )

    def search(self, request: SearchRequest):
        yield from QueueProcess(
            target=doctools.search_book, args=(self, request), name="bookworm-search"
        )


class BasePage(metaclass=ABCMeta):
    """Represents a page from the document."""

    __slots__ = ["document", "index"]

    def __init__(self, document: BaseDocument, index: int):
        self.document = document
        self.index = index

    @abstractmethod
    def get_text(self) -> str:
        """Return the text content or raise NotImplementedError."""

    @abstractmethod
    def get_image(self, zoom_factor: float, enhance: bool) -> t.Tuple[bytes, int, int]:
        """
        Return page image in the form of (image_data, width, height)
        or raise NotImplementedError.
        """

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


class FluidPage(BasePage):
    """Emulates a page for a fluid document."""

    def get_text(self):
        return self.document.get_content()

    def get_image(self, zoom_factor=1.0, enhance=False):
        raise NotImplementedError


class FluidDocument(BaseDocument):
    """Provides sain defaults for fluid documents."""

    def __len__(self):
        return 1

    def get_page(self, index: int) -> FluidPage:
        return FluidPage(self, index)

    @abstractmethod
    def get_content(self) -> str:
        """Get the content of this document."""
