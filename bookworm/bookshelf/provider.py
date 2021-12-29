# coding: utf-8

from __future__ import annotations
import attr
from abc import ABC, abstractmethod
from bookworm import typehints as t
from bookworm.document import DocumentInfo
from bookworm.logger import logger

log = logger.getChild(__name__)


class BookshelfProvider(ABC):

    name: t.str = None
    display_name: t.TranslatableStr = None
    __registered_providers = []

    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        if cls.name is not None:
            cls.__registered_providers.append(cls)

    @classmethod
    def get_providers(cls):
        return cls.__registered_providers

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

    @abstractmethod
    def get_source_actions(self) -> list[BookshelfAction]:
        """Get a list of actions supported by this source."""

    @abstractmethod
    def get_item_actions(self, item: DocumentInfo) -> list[BookshelfAction]:
        """Get a list of actions for the given item."""



class ContainerSource(Source):

    def __init__(self, *args, sources=None, source_actions=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.sources = sources
        self.source_actions = source_actions

    def iter_items(self) -> t.Iterator[Source]:
        yield from self.sources 

    def get_item_count(self):
        return len(self.sources)

    def get_source_actions(self):
        return self.source_actions

    def get_item_actions(self, item):
        raise NotImplementedError





@attr.s(auto_attribs=True, slots=True, frozen=True)
class BookshelfAction:
    display: t.TranslatableStr
    func: t.Callable[[Source, DocumentInfo], bool]
    decider: t.Callable[[Source, DocumentInfo], bool] = lambda doc_info: True

