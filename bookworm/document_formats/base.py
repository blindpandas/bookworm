# coding: utf-8

import gc
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from functools import wraps
from dataclasses import field, dataclass
from pycld2 import detect as detect_language, error as CLD2Error
from bookworm.concurrency import QueueProcess, call_threaded
from bookworm.utils import cached_property, generate_sha1hash_async
from bookworm.logger import logger
from . import _tools


log = logger.getChild(__name__)


class DocumentError(Exception):
    """The base class of all bookworm exceptions."""


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
    searching for a term in some book.
    """

    term: str
    case_sensitive: bool
    whole_word: bool
    from_page: int
    to_page: int


class PaginationError(IndexError):
    """Raised when the  `next` or `prev` page is not available."""


@dataclass(frozen=True)
class Pager:
    """A simple paginater."""

    __slots__ = ["first", "last", "current"]

    first: int
    last: int
    current: int

    def __post_init__(self):
        object.__setattr__(self, "current", self.first)

    def __repr__(self):
        return f"<Pagination: first={self.first}, last={self.last}, total={self.last - self.first}>"

    def __iter__(self):
        return iter(range(self.first, self.last + 1))

    def __len__(self):
        return self.last - self.first

    def __contains__(self, value):
        return self.first <= value <= self.last

    def reset(self):
        self.set_current(self.first)

    def set_current(self, to):
        if to not in self:
            raise PaginationError(f"The page ({to}) is out of range for this pager.")
        object.__setattr__(self, "current", to)

    def go_to_next(self):
        next_item = self.current + 1
        if next_item > self.last:
            raise PaginationError(f"Page ({next_item}) is out of range.")
        self.set_current(next_item)
        return next_item

    def go_to_prev(self):
        prev_item = self.current - 1
        if prev_item < self.first:
            raise PaginationError(f"Page ({prev_item}) is out of range.")
        self.set_current(prev_item)
        return prev_item


class Section:
    """A `Section` is a part of the book with
    a page range. It is commonly found in the
    TOC tree. It can contain other sections as well.
    """

    __slots__ = ["title", "parent", "children", "pager", "data"]

    def __init__(self, title, parent=None, children=None, pager=None, data=None):
        self.title = title
        self.parent = parent
        self.children = children or []
        self.pager = pager
        self.data = data or {}
        for child in self.children:
            child.parent = self

    def __getitem__(self, index):
        return self.children[index]

    def __len__(self):
        return len(self.children)

    def __contains__(self, item):
        return item in self.children

    def __bool__(self):
        return len(self) > 0

    def __repr__(self):
        return f"<{self.__class__.__name__}(title={self.title}, parent={getattr(self.parent, 'title', '')}, child_count={len(self)})>"

    def append(self, child):
        child.parent = self
        self.children.append(child)

    def iterchildren(self):
        for child in self.children:
            yield child
            yield from child.iterchildren()

    @property
    def is_root(self):
        return self.parent is None

    @property
    def first_child(self):
        if self:
            return self[0]

    @property
    def last_child(self):
        if self:
            return self[-1]

    @property
    def next_sibling(self):
        if self.is_root:
            return
        next_index = self.parent.children.index(self) + 1
        if next_index < len(self.parent):
            return self.parent[next_index]

    @property
    def prev_sibling(self):
        if self.is_root:
            return
        prev_index = self.parent.children.index(self) - 1
        if prev_index >= 0:
            return self.parent[prev_index]

    @property
    def simple_next(self):
        if self.next_sibling is not None:
            return self.next_sibling
        elif self.parent:
            return self.parent.simple_next

    @property
    def simple_prev(self):
        if self.prev_sibling is not None:
            return self.prev_sibling
        elif self.parent:
            return self.parent
        return self

    @property
    def unique_identifier(self):
        return f"{self.title}-{self.pager.first}-{self.pager.last}"


class BaseDocument(Sequence, metaclass=ABCMeta):

    format: str = None
    """The developer oriented format of this document."""

    name: str = None
    """The displayable name of this document format."""

    extensions: tuple = None
    """The file extension(s) of this format."""

    supports_rendering = False
    """Whether this document supports rendering its content visually."""

    def __init__(self, filename):
        self.filename = filename
        self._ebook = None
        super().__init__()

    def __contains__(self, value):
        return -1 < value < len(self)

    @cached_property
    def identifier(self):
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
        # XXX Is this a pre-mature optimization?
        call_threaded(lambda: self.language)

    @abstractmethod
    def close(self):
        """Perform the actual IO operations for unloading the ebook.
        Subclasses should call super to ensure the standard behavior.
        """
        self._ebook = None
        gc.collect()

    def is_encrypted(self):
        """Does this document need password."""
        return False

    @abstractmethod
    def decrypt(self, password):
        """Decrypt this document using the provided password."""

    @property
    @abstractmethod
    def toc_tree(self):
        """Return an iterable representing the table of content.
        The items should be of type `Section`.
        """

    @cached_property
    def language(self):
        """Return the language of this document.
        By default we use a heuristic based on Google's CLD2.
        """
        num_pages = len(self)
        num_samples = num_pages if num_pages <= 20 else 20
        text = "".join(self[i].getText() for i in range(num_samples)).encode("utf8")
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
    def metadata(self):
        """Return a `BookMetadata` object holding info about this book."""

    @abstractmethod
    def get_page_content(self, page_number):
        """Get the text content of a page."""

    @classmethod
    def export_to_text(cls, document_path, target_filename):
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
    def search(cls, document_path, request):
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

