# coding: utf-8

from abc import ABC, abstractmethod
from collections.abc import Collection
from bookworm import typehints as t
from bookworm.document import DocumentInfo
from bookworm.logger import logger

log = logger.getChild(__name__)

class BookshelfProvider:
    name: str = None
    display_name: t.TranslatableStr = None

    @abstractmethod
    def check(self) -> bool:
        """Checks the availability of this provider at runtime."""

    @abstractmethod
    def get_sources(self) -> list[Source]:
        """Return a list of sources for this provider."""


@attr.s(auto_attribs=True, slots=True)
class Source(Collection):
    name: str
    display_name: t.TranslatableStr

    def __iter__(self):
        yield from iter_items

    def __len__(self):
        return self.get_item_count()

    def __contains__(self, value):
        raise NotImplementedError

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



@attr.s(auto_atribs=True, slots=True, frozen=True)
class SourceAction:
    name: str
    display_name: t.TranslatableStr
    function: t.Callable[[Source, DocumentInfo], bool]


@attr.s(auto_attribs=True, slots=True)
class MetaSource:
    name: str
    display_name: t.TranslatableStr
    sources: t.Iterable[Source] = ()

    def add_source(self, source: Source):
        self.sources.append(source)

    def __iter__(self):
        yield from self.sources

    def __len__(self):
        return len(self.sources)

    def get_item_count(self):
        return sum(source.get_item_count() for source in self.sources)
