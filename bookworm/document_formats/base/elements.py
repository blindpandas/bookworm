# coding: utf-8

"""Provides value objects that are building blocks for an e-book."""

from dataclasses import field, dataclass
from collections.abc import Container, Iterable, Sequence, Sized
from weakref import ref
from bookworm import typehints as t
from bookworm.structured_text import TextRange


@dataclass
class BookMetadata:
    title: str
    author: str
    publisher: str = ""
    publication_year: str = ""
    isbn: str = ""
    additional_info: dict = field(default_factory=dict)


@dataclass
class SearchRequest:
    """
    Contains info about a search operation.
    """

    term: str
    is_regex: bool
    case_sensitive: bool
    whole_word: bool
    from_page: int
    to_page: int


@dataclass
class SearchResult:
    """Holds information about a single search result."""

    excerpt: str
    page: int
    position: int
    section: str


@dataclass(frozen=True, order=True)
class Pager(Container, Iterable, Sized):
    """Basically, this is a glorified `range` iterator."""

    __slots__ = ["first", "last"]

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

    __slots__ = [
        "documentref",
        "title",
        "parent",
        "children",
        "pager",
        "text_range",
        "level",
        "data",
    ]

    def __init__(
        self,
        document: "BaseDocument",
        title: str,
        parent: t.Optional["Section"] = None,
        children: t.Optional[t.List["Section"]] = None,
        pager: t.Optional[Pager] = None,
        text_range: t.Optional[TextRange] = None,
        level: t.Optional[int] = None,
        data: t.Optional[t.Dict[t.Hashable, t.Any]] = None,
    ):
        self.documentref = ref(document)
        self.title = title
        self.parent = parent
        self.children = children or []
        self.pager = pager
        self.text_range = text_range
        self.level = level
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
    def has_children(self):
        return bool(self)

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


class TreeStackBuilder(list):
    """
    Helps in building a tree of nodes with appropriate nesting.
    Use to build a toc tree consisting of `Section` nodes.
    """

    def __init__(self, root, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = root

    @property
    def top(self):
        return self[-1] if self else self.root

    @top.setter
    def top(self, value):
        self.append(value)

    def push(self, node):
        top_level, node_level = self.top.level, node.level
        if top_level < node_level:
            self.top.append(node)
            self.top = node
        elif top_level > node_level:
            top_node = self.top
            while self and (top_node.level > node.level):
                top_node = self.pop()
            return self.push(node)
        else:
            parent = self.top if self.top.is_root else self.top.parent
            parent.append(node)
            self.top = node


@dataclass
class ReadingOptions:
    reading_mode: str


SINGLE_PAGE_DOCUMENT_PAGER = Pager(first=0, last=0)
