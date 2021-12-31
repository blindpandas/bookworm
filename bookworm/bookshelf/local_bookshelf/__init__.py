# coding: utf-8

from __future__ import annotations
import winsound
from abc import ABC, abstractmethod
from functools import cached_property
from bookworm.document import DocumentInfo
from bookworm.logger import logger
from ..provider import BookshelfProvider, Source, ContainerSource, BookshelfAction
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
    display_name = _("Local Bookshelf")

    def check(self) -> bool:
        return True

    @classmethod
    def get_sources(self):
        retval = {}
        for table in (Category, Tag, Author):
            retval[table._meta.table_name] = tuple(
                LocalDatabaseSource(name=item.name, query=table.get_documents(item.name))
                for item in table.get_all()
            )
        return [
            ContainerSource(name=name, sources=sources,
                source_actions=[BookshelfAction("Add New", func=lambda s, v: True)]
            )
            for (name, sources) in retval.items()
        ]

    @classmethod
    def get_provider_actions(cls):
        return [
            SourceAction(_("Beep"), lambda: winsound.Beep(2000, 2000))
        ]

class LocalDatabaseSource(ABC, Source):
    def __init__(self, query, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query

    def iter_items(self) -> t.Iterator[DocumentInfo]:
        yield from self.get_items()

    def get_items(self):
        return [
            doc.as_document_info()
            for doc in self.query
        ]

    def get_item_count(self):
        return self.query.count()

    @classmethod
    def get_source_actions(cls):
        return [
            BookshelfAction("&Open", func=lambda doc_info, view: winsound.Beep(1000, 1000)),
            BookshelfAction("&Remove from bookshelf", func=lambda doc_info, view: 12),
        ]

    @classmethod
    def get_item_actions(cls, item):
        return [
            BookshelfAction("&Open", func=lambda doc_info, view: winsound.Beep(1000, 1000)),
            BookshelfAction("&Remove from bookshelf", func=lambda doc_info, view: 12),
            BookshelfAction("&Add to &Favorites", func=lambda doc_info, view: 42),
        ]
