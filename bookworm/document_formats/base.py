from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from dataclasses import field, dataclass
from weakref import WeakValueDictionary


@dataclass
class BookMetadata:
    title: str
    author: str
    publisher: str = ""
    publication_year: str = ""
    extra: dict = field(default_factory=dict)


class PaginationError(IndexError):
    """Raised when the  `next` or `prev` page is not available."""


@dataclass(frozen=True)
class Pager:
    """A simple paginater.""" 
    first: int
    last: int

    def __post_init__(self):
        self.reset()

    def __repr__(self):
        return f"<Pagination: first={self.first}, last={self.last}, total={self.last - self.first}>"

    def __iter__(self):
        return iter(range(self.first, self.last + 1))

    def __len__(self):
        return self.last - self.first

    def __contains__(self, value):
        return self.first <= value <= self.last

    def reset(self):
        object.__setattr__(self, "current",  self.first)

    def set_current(self, to):
        if  to not in self:
            raise PaginationError(f"The page ({to}) is out of range for this paginater.")
        object.__setattr__(self, "current",  to)

    @property
    def next(self):
        next_item = self.current + 1
        if next_item > self.last:
            raise PaginationError(f"Page ({next_item}) is out of range.")
        object.__setattr__(self, "current",  next_item)
        return next_item

    @property
    def prev(self):
        prev_item = self.current - 1
        if prev_item < self.first:
            raise PaginationError(f"Page ({prev_item}) is out of range.")
        object.__setattr__(self, "current",  prev_item)
        return prev_item


@dataclass
class TOCItem:
    title: str
    children: list = field(default_factory=list)
    data: dict = field(default_factory=dict)

@dataclass
class PaginatedTOCItem:
    title: str
    pager: Pager = None
    children: list = field(default_factory=list)
    data: dict = field(default_factory=dict)


class BaseDocument(metaclass=ABCMeta):

    # Important Attributes
    # Must be defined in all subclasses
    format: str = None
    name: str = None
    extensions: tuple = None

    # Flags, set as needed.
    supports_pagination = False

    def __init__(self, ebook_path):
        self.ebook_path = ebook_path
        self._ebook = None
        super().__init__()

    @abstractmethod
    def read(self):
        """Perform the actual IO operations for loading the ebook."""

    @abstractmethod
    def close(self):
        """Perform the actual IO operations for unloading the ebook."""
        self._ebook = None

    @abstractmethod
    def get_content(self, item):
        """Get the text content for an item."""

    @property
    @abstractmethod
    def toc_tree(self):
        """Return an iterable representing the table of content.
        The items should be of type `TOCItem`.
        """

    @property
    @abstractmethod
    def metadata(self):
        """Return a `Book` object holding info about this book."""


class PaginatedBaseDocument(BaseDocument, Sequence):
    """A Base Document that supports pagination."""
    supports_pagination = True

    def __contains__(self, value):
        return 0 <= value < len(self)

    @abstractmethod
    def get_page_content(self, page_number):
        """Get the text content of a page."""

    @property
    def paginated_toc_tree(self):
        return self._get_paginated_toc_tree()
    
    def _get_paginated_toc_tree(self, items=None, rv=None):
        if items is rv is None:
            rv = {}
            items = self.toc_tree[1:]
        for item in items:
            pgn = item.pager
            rv[(pgn.first, pgn.last)] = item
            if item.children:
                self._get_paginated_toc_tree(item.children, rv)
        return rv
