# coding: utf-8

from __future__ import annotations
import attr
from abc import ABC, abstractmethod
from functools import cached_property
from bookworm import typehints as t
from bookworm.image_io import ImageIO
from bookworm.paths import images_path
from bookworm.document import DocumentInfo
from bookworm.signals import _signals
from bookworm.logger import logger

log = logger.getChild(__name__)


sources_updated = _signals.signal("bookshelf/source_updated")


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
        return [prov() for prov in cls.__registered_providers if prov.check()]

    def __iter__(self):
        yield from self.iter_items()

    def __len__(self):
        return len(self.sources)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    @classmethod
    @abstractmethod
    def check(self) -> bool:
        """Checks the availability of this provider at runtime."""
        return True

    @abstractmethod
    def get_sources(self) -> list[t.ForwardRef("Source")]:
        """Return a list of sources for this provider."""

    @abstractmethod
    def get_provider_actions(self) -> list[t.ForwardRef("SourceAction")]:
        """Return a list of actions supported by this provider."""


class Source:
    """Represent a bookshelf source."""

    can_rename_items = False

    def __init__(
        self,
        provider,
        name: t.TranslatableStr,
        sources=(),
        *,
        source_actions=(),
        item_actions=(),
        data=None,
    ):
        self.provider = provider
        self.name = name
        self.sources = sources
        self.source_actions = source_actions
        self.item_actions = item_actions
        self.data = data if data is not None else {}

    def get_items(self):
        return self.sources

    def __iter__(self):
        yield from self.iter_items()

    def __len__(self):
        return self.get_item_count()

    def iter_items(self) -> t.Iterator[DocumentInfo]:
        """Return a list of documents contained in this source."""
        yield from self.get_items()

    @abstractmethod
    def get_item_count(self):
        """Return the number of documents in this source."""

    def get_source_actions(self) -> list[BookshelfAction]:
        """Get a list of actions supported by this source."""
        return self.source_actions

    def get_item_actions(self, item: DocumentInfo) -> list[BookshelfAction]:
        """Get a list of actions for the given item."""
        return self.item_actions

    def resolve_item_uri(self, item):
        return item.uri

    def change_item_title(self, item, new_title):
        pass

    def is_valid(self):
        return True


class MetaSource(Source):
    """Represents a source that merely groups other sources."""

    def get_item_count(self):
        return len([item for item in self.get_items() if item.is_valid()])

    def get_item_actions(self, item):
        raise NotImplementedError


class ItemContainerSource(MetaSource):
    """Represents a source that groups other sources and items (i.e a directory)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = self.name

    @cached_property
    def cover_image(self):
        return ImageIO.from_filename(images_path("folder.png"))


@attr.s(auto_attribs=True, slots=True, frozen=True)
class BookshelfAction:
    display: t.TranslatableStr
    func: t.Callable[[Source, DocumentInfo], bool]
    decider: t.Callable[[Source, DocumentInfo], bool] = lambda doc_info: True
