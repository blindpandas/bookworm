# coding: utf-8

import gc
from abc import ABCMeta, abstractmethod
from collections.abc import Container, Iterable, Sequence, Sized
from enum import IntFlag
from functools import wraps
from dataclasses import field, dataclass
from weakref import ref
from lru import LRU
from pycld2 import detect as detect_language, error as CLD2Error
from bookworm import typehints as t
from bookworm.concurrency import QueueProcess, call_threaded
from bookworm.utils import cached_property, generate_sha1hash_async
from bookworm.logger import logger
from . import _tools


log = logger.getChild(__name__)
PAGE_CACHE_CAPACITY = 100


class DocumentError(Exception):
    """The base class of all document related exceptions."""


class PaginationError(DocumentError, IndexError):
    """Raised when the  `next` or `prev` page is not available."""



@dataclass
class BookMetadata:
    title: str
    author: str
    publisher: str = ""
    publication_year: str = ""
    additional_info: dict = field(default_factory=dict)


@dataclass
class SearchRequest:
    """Holds information of a user's request for
    searching for a term in a book.
    """

    term: str
    is_regex: bool
    case_sensitive: bool
    whole_word: bool
    from_page: int
    to_page: int


@dataclass(frozen=True, order=True)
class Pager(Container, Iterable, Sized):
    """Basically, this is a glorified `range` iterator."""

    __slots__ = ["first", "last",]

    first: int
    last: int

    def __repr__(self):
        return f"<Pager: first={self.first}, last={self.last}, total={self.last - self.first}>"

    def __iter__(self) -> t.Iterable[int]:
        return iter(range(self.first, self.last + 1))

    def __len__(self):
        return self.last - self.first

    def __contains__(self, value):
        return self.first <= value <= self.last

    def __hash__(self):
        return hash((self.first, self.last))


class Section:
    """
    A simple (probably inefficient) custom tree
    implementation for use in the table of content.
    """

    __slots__ = ["documentref", "title", "parent", "children", "pager", "data"]

    def __init__(
        self,
        document: "BaseDocument",
        title: str,
        parent: t.Optional["Section"]=None,
        children: t.Optional[t.List["Section"]]=None,
        pager: t.Optional[Pager]=None,
        data: t.Optional[t.Dict[t.Hashable, t.Any]]=None
        ):
        self.documentref = ref(document)
        self.title = title
        self.parent = parent
        self.children = children or []
        self.pager = pager
        self.data = data or {}
        for child in self.children:
            child.parent = self

    def __getitem__(self, index: int) -> "Section":
        return self.children[index]

    def __len__(self):
        return len(self.children)

    def __contains__(self, item: "Section"):
        return item in self.children

    def __bool__(self):
        return len(self) > 0

    def __repr__(self):
        return f"<{self.__class__.__name__}(title={self.title}, parent={getattr(self.parent, 'title', '')}, child_count={len(self)})>"

    def append(self, child: "Section"):
        child.parent = self
        self.children.append(child)

    def iter_children(self) -> t.Iterable["Section"]:
        for child in self.children:
            yield child
            yield from child.iter_children()

    def iter_pages(self) -> t.Iterable["BasePage"]:
        document = self.documentref()
        if document is not None:
            for index in self.pager:
                yield document[index]
        else:
            raise RuntimeError("Document ref is dead!")

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def first_child(self) -> t.Optional["Section"]:
        if self:
            return self[0]

    @property
    def last_child(self) -> t.Optional["Section"]:
        if self:
            return self[-1]

    @property
    def next_sibling(self) -> t.Optional["Section"]:
        if self.is_root:
            return
        next_index = self.parent.children.index(self) + 1
        if next_index < len(self.parent):
            return self.parent[next_index]

    @property
    def prev_sibling(self) -> t.Optional["Section"]:
        if self.is_root:
            return
        prev_index = self.parent.children.index(self) - 1
        if prev_index >= 0:
            return self.parent[prev_index]

    @property
    def simple_next(self) -> t.Optional["Section"]:
        if self.next_sibling is not None:
            return self.next_sibling
        elif self.parent:
            return self.parent.simple_next

    @property
    def simple_prev(self) -> t.Optional["Section"]:
        if self.prev_sibling is not None:
            return self.prev_sibling
        elif self.parent:
            return self.parent
        return self

    @property
    def unique_identifier(self) -> str:
        return f"{self.title}-{self.pager.first}-{self.pager.last}"


class DocumentCapability(IntFlag):
    """Represents feature flags for a document.""" 
    TOC_TREE = 1
    METADATA = 2
    GRAPHICAL_RENDERING = 3
    FLUID_PAGINATION = 4
    IMAGE_EXTRACTION = 5


class BaseDocument(Sequence, metaclass=ABCMeta):

    format: str = None
    """The developer oriented format of this document."""

    name: str = None
    """The displayable name of this document format."""

    extensions: tuple = None
    """The file extension(s) of this format."""

    capabilities: DocumentCapability = ()
    """A combination of DocumentCapability flags."""

    def __init__(self, filename: t.PathLike):
        self.filename = filename
        self._ebook: t.Any = None
        super().__init__()

    def __contains__(self, value: int):
        return -1 < value < len(self)

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
        self._sha1hash = generate_sha1hash_async(self.filename)
        self.__page_cache = LRU(PAGE_CACHE_CAPACITY)
        # XXX Is this a pre-mature optimization?
        call_threaded(lambda: self.language)

    @abstractmethod
    def close(self):
        """Perform the actual IO operations for unloading the ebook.
        Subclasses should call super to ensure the standard behavior.
        """
        self._ebook = None
        self.__page_cache.clear()
        gc.collect()

    def is_encrypted(self) -> bool:
        """Does this document need password."""
        return False

    @abstractmethod
    def decrypt(self, password):
        """Decrypt this document using the provided password."""

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
        _cached = self.__page_cache.get(page_number)
        if _cached is not None:
            return _cached
        content = self[page_number].get_text()
        self.__page_cache[page_number] = content
        return content

    def get_page_image(self, page_number: int, zoom_factor: float=1.0, enhance: bool=False) -> bytes:
        """Convenience method: return the image of a page."""
        return self[page_number].get_image(zoom_factor, enhance)

    @classmethod
    def export_to_text(cls, document_path: t.PathLike, target_filename: t.PathLike):
        args = (cls, document_path, target_filename)
        process = QueueProcess(
            target=_tools.do_export_to_text, args=args, name="bookworm-exporter"
        )
        process.start()
        while True:
            value = process.queue.get()
            if value == -1:
                break
            yield value
        process.join()

    @classmethod
    def search(cls, document_path: t.PathLike, request: SearchRequest):
        args = (cls, document_path, request)
        process = QueueProcess(
            target=_tools.do_search_book, args=args, name="bookworm-search"
        )
        process.start()
        while True:
            value = process.queue.get()
            if value == -1:
                break
            yield value
        process.join()


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
        """Return page image in the form of (image_data, width, height)
        or raise NotImplementedError."""

    @property
    def number(self) -> int:
        """The user facing page number."""
        return self.index + 1

    @cached_property
    def section(self) -> Section:
        rv = self.document.toc_tree
        for sect in rv.iter_children():
            if self.index in sect.pager and not sect:
                rv = sect
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
