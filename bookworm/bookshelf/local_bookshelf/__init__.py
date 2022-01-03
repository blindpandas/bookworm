# coding: utf-8

from __future__ import annotations
import wx
import winsound
import peewee
from abc import ABC, abstractmethod
from functools import cached_property
from bookworm.signals import app_booting
from bookworm.document import DocumentInfo
from bookworm.logger import logger
from ..provider import (
    BookshelfProvider,
    Source,
    MetaSource,
    ItemContainerSource,
    BookshelfAction,
    sources_updated,
    items_updated,
)
from .models import (
    BaseModel,
    Document,
    Author,
    Category,
    Tag,
    DocumentFTSIndex,
)

log = logger.getChild(__name__)


@app_booting.connect
def create_db_tables(sender):
    BaseModel.create_all()


class LocalBookshelfProvider(BookshelfProvider):

    name = "local_bookshelf"
    display_name = _("Local Bookshelf")

    @classmethod
    def check(cls) -> bool:
        return True

    @classmethod
    def _create_local_database_sources_from_model(cls, model):
        remove_source_action = BookshelfAction(
            _("Remove..."),
            func=cls._on_remove_source,
        )
        change_name_action = BookshelfAction(
            _("Edit name..."),
            func=cls._on_change_name,
        )
        return [
            LocalDatabaseSource(
                provider=cls,
                name=item.name,
                query=model.get_documents(item.name),
                model=model,
                source_actions=[change_name_action, remove_source_action]
            )
            for item in model.get_all()
        ]

    @classmethod
    def get_sources(cls):
        sources = [
            LocalDatabaseSource(
                provider=cls,
                name=_("Favorites"),
                query=Document.select().where(Document.is_favorite == True),
                source_actions=[]
            ),
            LocalDatabaseSource(
                provider=cls,
                name=_("Recents"),
                query=Document.select().order_by(Document.date_added.desc()).limit(100),
                source_actions=[]
            )
        ]
        classifications = {
            _("Categories"): (cls._create_local_database_sources_from_model(Category), Category),
            _("Tags"): (cls._create_local_database_sources_from_model(Tag), Tag),
        }
        add_new_action = BookshelfAction(
            _("Add New..."),
            func=cls._on_add_new,
        )
        sources += [
            MetaSource(
                provider=cls,
                name=name,
                sources=srcs,
                source_actions=[add_new_action,],
                data={'model': model}
            )
            for (name, (srcs, model)) in classifications.items()
        ]
        author_sources = [
            LocalDatabaseSource(
                provider=cls,
                name=item.name,
                query=Author.get_documents(item.name),
                model=Author,
            )
            for item in Author.get_all()
        ]
        sources += [
            MetaSource(
                provider=cls,
                name=_("Authors"),
                sources=author_sources,
                data={'model': Author}
            )
        ]
        return sources

    @classmethod
    def get_provider_actions(cls):
        return [
            SourceAction(_("Beep"), lambda: winsound.Beep(2000, 2000))
        ]

    @classmethod
    def _on_change_name(cls, source):
        instance = source.model.get(name=source.name)
        old_name = instance.name
        new_name = wx.GetTextFromUser(
            _("New name:"),
            _("Edit Name"),
            default_value=old_name
        ).strip()
        if new_name and (new_name != old_name):
            instance.name = new_name
            try:
                instance.save()
            except peewee.IntegrityError:
                wx.MessageBox(
                    _("The given name {name} already exists.\nPlease choose another name.").format(name=new_name),
                    _("Duplicate name"),
                    style=wx.ICON_WARNING
                )
                cls._on_change_name(source)
            else:
                sources_updated.send(cls)

    @classmethod
    def _on_remove_source(cls, source):
        retval = wx.MessageBox(
            _("Are you sure you want to remove {name}?\nThis will not remove document classified under {name}.").format(name=source.name),
            _("Confirm"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION
        )
        if retval == wx.YES:
            instance = source.model.get(name=source.name)
            source.model.delete_instance(instance)
            sources_updated.send(cls)

    @classmethod
    def _on_add_new(cls, source):
        new_name = wx.GetTextFromUser(
            _("Enter name:"),
            _("Add New"),
        )
        source.data['model'].get_or_create(name=new_name)
        sources_updated.send(cls)


class LocalDatabaseSource(Source):
    def __init__(self, query, *args, model=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.model = model

    def iter_items(self) -> t.Iterator[DocumentInfo]:
        yield from self.get_items()

    def get_items(self):
        return [
            doc.as_document_info()
            for doc in self.query
        ]

    def get_item_count(self):
        return self.query.count()

    def get_item_actions(self, item):
        doc_instance = Document.get(item.data['database_id'])
        retval = [
            BookshelfAction(
                _("Remove from &Favorites") if doc_instance.is_favorite else _("Add to &Favorites"),
                func=lambda doc_info: self._toggle_favorite_status(doc_instance)
            ),
            BookshelfAction(
                _("Edit category..."),
                func=lambda doc_info: self._do_edit_category(doc_instance)
            ),
            BookshelfAction(
                _("Edit tags..."),
                func=lambda doc_info: self._do_edit_tags(doc_instance)
            ),
            BookshelfAction(
                _("Remove from bookshelf"),
                func=lambda doc_info: self._do_remove_from_bookshelf(doc_instance)
            ),
        ]
        return retval

    def _toggle_favorite_status(self, doc_instance):
        doc_instance.is_favorite = not doc_instance.is_favorite
        doc_instance.save()

    def _do_remove_from_bookshelf(self, doc_instance):
        retval = wx.MessageBox(
            _("Are you sure you want to remove this document from your bookshelf?\nTitle: {title}\nThis will remove the document from all tags and categories.").format(title = doc_instance.title),
            _("Remove From Bookshelf?"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION
        )
        if retval == wx.YES:
            doc_instance.delete_instance()
            sources_updated.send(self.provider)

