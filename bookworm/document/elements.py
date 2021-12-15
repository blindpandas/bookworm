# coding: utf-8

"""Provides value objects that are building blocks for an e-book."""

from __future__ import annotations
import attr
from collections.abc import Container, Iterable, Sequence, Sized
from weakref import ref
from datetime import datetime
from bookworm import typehints as t
from bookworm.structured_text import TextRange


@attr.s(auto_attribs=True, slots=True)
class BookMetadata:
    title: str
    author: str
    publisher: str = ""
    publication_year: str = ""
    isbn: str = ""
    additional_info: dict = attr.ib(factory=dict)


@attr.s(auto_attribs=True, slots=True)
class Pager(Container, Iterable, Sized):
    """Basically, this is a glorified `range` iterator."""

    first: int
    last: int

    def __iter__(self) -> t.Iterable[int]:
        return iter(range(self.first, self.last + 1))

    def __len__(self):
        return self.last - self.first

    def __contains__(self, value):
        return self.first <= value <= self.last

    def astuple(self):
        return (self.first, self.last)


@attr.s(auto_attribs=True, repr=False, slots=True)
class Section:
    """
    A simple (probably inefficient) custom tree
    implementation for use in the table of content.
    """

    title: str
    parent: t.ForwardRef("Section") = None
    children: list[t.ForwardRef("Section")] = attr.ib(factory=list)
    pager: Pager = None
    text_range: TextRange = None
    level: int = None
    data: t.Dict[t.Any, t.Any] = attr.ib(factory=dict)

    def __attrs_post_init__(self):
        for child in self.children:
            child.parent = self

    def __getitem__(self, index: int) -> Section:
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

    def iter_children(self) -> t.Iterable[Section]:
        for child in self.children:
            yield child
            yield from child.iter_children()

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def has_children(self):
        return bool(self)

    @property
    def first_child(self) -> t.Optional[Section]:
        if self:
            return self[0]

    @property
    def last_child(self) -> t.Optional[Section]:
        if self:
            return self[-1]

    @property
    def next_sibling(self) -> t.Optional[Section]:
        if self.is_root:
            return
        next_index = self.parent.children.index(self) + 1
        if next_index < len(self.parent):
            return self.parent[next_index]

    @property
    def prev_sibling(self) -> t.Optional[Section]:
        if self.is_root:
            return
        prev_index = self.parent.children.index(self) - 1
        if prev_index >= 0:
            return self.parent[prev_index]

    @property
    def simple_next(self) -> t.Optional[Section]:
        if self.next_sibling is not None:
            return self.next_sibling
        elif self.parent:
            return self.parent.simple_next

    @property
    def simple_prev(self) -> t.Optional[Section]:
        if self.prev_sibling is not None:
            return self.prev_sibling
        elif self.parent:
            return self.parent
        return self

    @property
    def unique_identifier(self) -> str:
        return f"{self.title}-{self.pager.first}-{self.pager.last}"


@attr.s(auto_attribs=True, slots=True, frozen=True)
class LinkTarget:
    url: str
    is_external: bool
    page: int = None
    position: int = None


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
        return node


@attr.s(auto_attribs=True, slots=True)
class ReadingOptions:
    reading_mode: str


@attr.s(auto_attribs=True, slots=True, frozen=True, kw_only=True)
class DocumentInfo:
    """Holds information about an unloaded document."""

    uri: DocumentUri
    title: str
    number_of_pages: int = None
    number_of_sections: int = None
    authors: list[str] = ()
    publication_date: t.Union[datetime, str] = None
    publisher: str = ""
    cover_image: ImageIO = None
    data: dict[t.Any, t.Any] = attr.ib(factory=dict)

    @classmethod
    def from_document(cls, document):
        metadata = document.metadata
        return cls(
            uri=document.uri,
            title=metadata.title,
            number_of_pages=len(document),
            number_of_sections=len(document.toc_tree),
            authors=metadata.author,
            publication_date=metadata.publication_year,
            publisher=metadata.publisher,
            cover_image=document.get_cover_image()
        )

SINGLE_PAGE_DOCUMENT_PAGER = Pager(first=0, last=0)

