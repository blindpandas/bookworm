# coding: utf-8

from __future__ import annotations
import urllib.parse
import requests
import wx
import peewee
from abc import ABC, abstractmethod
from functools import cached_property
from bookworm import local_server
from bookworm.signals import app_booting
from bookworm.document import DocumentInfo
from bookworm.logger import logger
from .tasks import ADD_TO_BOOKSHELF_URL_PREFIX, IMPORT_FOLDER_TO_BOOKSHELF_URL_PREFIX
from ..provider import (
    BookshelfProvider,
    Source,
    MetaSource,
    ItemContainerSource,
    BookshelfAction,
    sources_updated,
)
from .models import (
    BaseModel,
    Document,
    Author,
    Category,
    Tag,
    DocumentTag,
    DocumentFTSIndex,
)
from .dialogs import EditDocumentClassificationDialog, AddFolderToLocalBookshelfDialog


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

    def _create_local_database_sources_from_model(self, model):
        remove_source_action = BookshelfAction(
            _("Remove..."),
            func=self._on_remove_source,
        )
        change_name_action = BookshelfAction(
            _("Edit name..."),
            func=self._on_change_name,
        )
        remove_related_documents_action = BookshelfAction(
            _("Remove Related Documents..."),
            func=self._on_remove_related_documents,
            decider=lambda source: source.get_item_count() > 0
        )
        return [
            LocalDatabaseSource(
                provider=self,
                name=item.name,
                query=model.get_documents(item.name),
                model=model,
                source_actions=[change_name_action, remove_related_documents_action, remove_source_action]
            )
            for item in model.get_all()
        ]

    def get_sources(self):
        sources = [
            LocalDatabaseSource(
                provider=self,
                name=_("Recents"),
                query=Document.select().order_by(Document.date_added.desc()).limit(100),
                source_actions=[]
            ),
            LocalDatabaseSource(
                provider=self,
                name=_("Favorites"),
                query=Document.select().where(Document.is_favorite == True),
                source_actions=[]
            ),
        ]
        classifications = {
            _("Categories"): (self._create_local_database_sources_from_model(Category), Category),
            _("Tags"): (self._create_local_database_sources_from_model(Tag), Tag),
        }
        add_new_action = BookshelfAction(
            _("Add New..."),
            func=self._on_add_new,
        )
        sources += [
            MetaSource(
                provider=self,
                name=name,
                sources=srcs,
                source_actions=[add_new_action,],
                data={'model': model}
            )
            for (name, (srcs, model)) in classifications.items()
        ]
        sources += [
            AuthorMetaSource(
                provider=self,
                name=_("Authors"),
                data={'model': Author},
                sources=None
            )
        ]
        return sources

    def get_provider_actions(self):
        return [
            BookshelfAction(_("Import documents from folder..."), func=self._on_add_documents_from_folder)
        ]

    def _on_add_documents_from_folder(self, provider):
        top_frame = wx.GetApp().GetTopWindow()
        dialog = AddFolderToLocalBookshelfDialog(
            top_frame,
            _("Import Documents From Folder"),
        )
        with dialog:
            retval = dialog.ShowModal()
        if retval is None:
            return
        folder, category_name = retval
        url = urllib.parse.urljoin(
            local_server.get_local_server_netloc(),
            IMPORT_FOLDER_TO_BOOKSHELF_URL_PREFIX
        )
        res = requests.post(
            url,
            json={'folder': folder, 'category_name': category_name}
        )
        log.debug(f"Add folder to bookshelf response: {res}")

    def _on_change_name(self, source):
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
                self._on_change_name(source)
            else:
                sources_updated.send(self, update_sources=True)

    def _on_remove_source(self, source):
        retval = wx.MessageBox(
            _("Are you sure you want to remove {name}?\nThis will not remove document classified under {name}.").format(name=source.name),
            _("Confirm"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION
        )
        if retval == wx.YES:
            instance = source.model.get(name=source.name)
            source.model.delete_instance(instance)
            sources_updated.send(self, update_sources=True)

    def _on_remove_related_documents(self, source):
        retval = wx.MessageBox(
            _("Are you sure you want to remove all documents classified under {name}?\nThis will remove those documents from your bookshelf.").format(name=source.name),
            _("Confirm"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION
        )
        if retval == wx.YES:
            for item in source:
                Document.delete().where(Document.id == item.data['database_id']).execute()
            sources_updated.send(self, update_items=True)

    def _on_add_new(self, source):
        new_name = wx.GetTextFromUser(
            _("Enter name:"),
            _("Add New"),
        )
        source.data['model'].get_or_create(name=new_name)
        sources_updated.send(self, update_sources=True)


class LocalDatabaseSource(Source):
    def __init__(self, query, *args, model=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.model = model

    def get_items(self):
        return [
            doc.as_document_info()
            for doc in self.query.clone()
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
                _("Edit category / Tags..."),
                func=lambda doc_info: self._do_edit_category_and_tags(doc_instance)
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
        sources_updated.send(self.provider, update_items=True)

    def _do_edit_category_and_tags(self, doc_instance):
        top_frame = wx.GetApp().GetTopWindow()
        dialog = EditDocumentClassificationDialog(
            top_frame,
            title=_("Edit Category/Tags"),
            categories=[cat.name for cat in Category.get_all()],
            given_category=None if not doc_instance.category else doc_instance.category.name,
            tags_names=[
                Tag.get_by_id(doc_tag.tag_id).name
                for doc_tag in DocumentTag.select().where(DocumentTag.document_id == doc_instance.get_id())
            ]
        )
        with dialog:
            if (retval := dialog.ShowModal()) is None:
                return
            category_name, tags_names = retval
            anything_created = doc_instance.change_category_and_tags(category_name, tags_names)
            sources_updated.send(self.provider, update_sources=anything_created, update_items=True)

    def _do_remove_from_bookshelf(self, doc_instance):
        retval = wx.MessageBox(
            _("Are you sure you want to remove this document from your bookshelf?\nTitle: {title}\nThis will remove the document from all tags and categories.").format(title = doc_instance.title),
            _("Remove From Bookshelf?"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION
        )
        if retval == wx.YES:
            doc_instance.delete_instance()
            sources_updated.send(self.provider, update_items=True)

   


class AuthorMetaSource(MetaSource):

    def get_items(self):
        return [
            AuthorLocalDatabaseSource(
                provider=self.provider,
                name=item.name,
                query=Author.get_documents(item.name),
                model=Author,
            )
            for item in Author.get_all()
        ]


class AuthorLocalDatabaseSource(LocalDatabaseSource):

    def is_valid(self):
        return self.get_item_count() != 0
