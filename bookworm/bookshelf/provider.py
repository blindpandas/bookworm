# coding: utf-8

from __future__ import annotations
import attr
from abc import ABC, abstractmethod
from bookworm import typehints as t
from bookworm.document import DocumentInfo
from bookworm.logger import logger

log = logger.getChild(__name__)


class BookshelfProvider:
    def __init__(self, name: str, display_name: t.TranslatableStr, sources=None):
        self.name = name
        self.display_name = display_name
        self.sources = sources

    def __iter__(self):
        yield from self.get_sources()

    def __len__(self):
        return len(self.sources)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    @abstractmethod
    def check(self) -> bool:
        """Checks the availability of this provider at runtime."""

    @classmethod
    def get_sources(
        cls,
    ) -> list[t.Union[t.ForwardRef("Source"), t.ForwardRef("BookshelfProvider")]]:
        """Return a list of sources for this provider."""
        return self.sources


class Source:
    """Represent a bookshelf source."""

    def __init__(self, name: t.TranslatableStr):
        self.name = name

    def __iter__(self):
        yield from self.iter_items()

    def __len__(self):
        return self.get_item_count()

    @abstractmethod
    def iter_items(self) -> t.Iterator[DocumentInfo]:
        """Return a list of documents contained in this source."""

    @abstractmethod
    def get_item_count(self):
        """Return the number of documents in this source."""

    @classmethod
    @abstractmethod
    def get_source_actions(cls) -> list[SourceAction]:
        """Get a list of actions supported by this source."""

    @abstractmethod
    def get_item_actions(self, item: DocumentInfo) -> list[SourceAction]:
        """Get a list of actions for the given item."""


@attr.s(auto_attribs=True, slots=True, frozen=True)
class SourceAction:
    name: str
    display_name: t.TranslatableStr
    function: t.Callable[[Source, DocumentInfo], bool]
