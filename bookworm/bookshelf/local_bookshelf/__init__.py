# coding: utf-8

from __future__ import annotations
from abc import ABC, abstractmethod
from functools import cached_property
from bookworm.document import DocumentInfo
from bookworm.logger import logger
from ..provider import Source, BookshelfProvider, SourceAction
from .models import (
    Document,
    Author,
    Category,
    Tag,
    DocumentFTSIndex,
)

log = logger.getChild(__name__)


class LocalBookshelfProvider(BookshelfProvider):

    name = "local_bookshelf"
    display_name = _("Your Bookshelf")

    def check(self) -> bool:
        return True

    @classmethod
    def get_sources(self):
        retval = {}
        for table in (Category, Tag, Author):
            retval[table._meta.table_name] = tuple(
                LocalDatabaseSource(name=table.name, query=Document.select())
                for item in table.select(table.name).distinct()
            )
        return [
            LocalBookshelfProvider(name=name, display_name=name, sources=sources)
            for (name, sources) in retval.items()
        ]


class LocalDatabaseSource(ABC, Source):
    def __init__(self, query, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query

    def iter_items(self) -> t.Iterator[DocumentInfo]:
        yield from self.query

    def get_item_count(self):
        return self.query.count()

    @classmethod
    def get_source_actions(cls) -> list[SourceAction]:
        return []

    def get_item_actions(self, item: DocumentInfo) -> list[SourceAction]:
        return []
