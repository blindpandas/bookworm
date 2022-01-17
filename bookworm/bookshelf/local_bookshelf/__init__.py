# coding: utf-8

from __future__ import annotations
import math
import os
import wx
import peewee
from abc import ABC, abstractmethod
from functools import partial, cached_property
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from bookworm import config
from bookworm.signals import app_booting
from bookworm.document import DocumentInfo
from bookworm.document.uri import DocumentUri
from bookworm.gui.components import AsyncSnakDialog
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.logger import logger
from ..provider import (
    BookshelfProvider,
    Source,
    MetaSource,
    ItemContainerSource,
    BookshelfAction,
    sources_updated,
)
from .dialogs import (
    EditDocumentClassificationDialog,
    AddFolderToLocalBookshelfDialog,
    SearchBookshelfDialog,
    BookshelfSearchResultsDialog,
    BundleErrorsDialog,
)
from .tasks import issue_import_folder_request, add_document_to_bookshelf, bundle_single_document
from .models import (
    DEFAULT_BOOKSHELF_DATABASE_FILE,
    BaseModel,
    Document,
    Author,
    Category,
    Tag,
    DocumentTag,
    DocumentAuthor,
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
                name=_("Recently Added"),
                query=Document.select().order_by(Document.date_added.desc()).limit(10),
                source_actions=[]
            ),
            LocalDatabaseSource(
                provider=self,
                name=_("Currently Reading"),
                query=Document.select().where(Document.is_currently_reading == True).order_by(Document.title.asc()),
                source_actions=[]
            ),
            LocalDatabaseSource(
                provider=self,
                name=_("Want to read"),
                query=Document.select().where(Document.in_reading_list == True).order_by(Document.title.asc()),
                source_actions=[]
            ),
            LocalDatabaseSource(
                provider=self,
                name=_("Favorites"),
                query=Document.select().where(Document.favorited == True).order_by(Document.title.asc()),
                source_actions=[]
            ),
        ]
        classifications = [
            (_("Reading Lists"), (self._create_local_database_sources_from_model(Category), Category)),
            (_("Collections"), (self._create_local_database_sources_from_model(Tag), Tag)),
        ]
        classifications[0][1][0].append(
            InvalidIfEmptyLocalDatabaseSource(
                provider=self,
                name=_("General"),
                query=Document.select().where(Document.category == None).order_by(Document.title.asc()),
                source_actions=[]
            ),
        )
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
            for (name, (srcs, model)) in classifications
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
            BookshelfAction(_("Import Documents...\tCtrl+O"), func=self._on_import_document),
            BookshelfAction(_("Import documents from folder..."), func=self._on_add_documents_from_folder),
            BookshelfAction(_("Search Bookshelf..."), func=self._on_search_bookshelf),
            BookshelfAction(_("Bundle Documents..."), func=self._on_bundle_documents),
        ]

    def _on_import_document(self, provider):
        last_folder = config.conf["history"]["last_folder"]
        if not os.path.isdir(last_folder):
            last_folder = str(Path.home())
        openFileDlg = wx.FileDialog(
            wx.GetApp().GetTopWindow(),
            # Translators: the title of a file dialog to browse to a document
            message=_("Import Documents To Bookshelf"),
            defaultDir=last_folder,
            wildcard=BookViewerWindow._get_ebooks_wildcards(),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
        )
        if openFileDlg.ShowModal() != wx.ID_OK:
            return
        filenames = [
            filename
            for filename in openFileDlg.GetPaths()
            if os.path.isfile(filename)
        ]
        openFileDlg.Destroy()
        if not filenames:
            return
        dialog = EditDocumentClassificationDialog(
            wx.GetApp().GetTopWindow(),
            title=_("Edit reading list/collections"),
            categories=[cat.name for cat in Category.get_all()],
        )
        with dialog:
            if (retval := dialog.ShowModal()) is not None:
                category_name, tags_names = retval
            else:
                return
        task = partial(
            self._do_add_files_to_bookshelf,
            filenames,
            category_name=category_name,
            tags_names=tags_names
        )
        message = (
            _("Importing document...")
            if len(filenames) == 1
            else _("Importing documents...")
        )
        AsyncSnakDialog(
            task=task,
            done_callback=self._on_document_imported_callback,
            message=message,
            parent=wx.GetApp().GetTopWindow()
        )

    def _do_add_files_to_bookshelf(self, filenames, category_name, tags_names):
        for filename in filenames:
            add_document_to_bookshelf(
                DocumentUri.from_filename(filename),
                category_name=category_name,
                tags_names=tags_names,
                database_file=DEFAULT_BOOKSHELF_DATABASE_FILE
            )

    def _on_document_imported_callback(self, future):
        try:
            future.result()
        except Exception as e:
            log.exception("Failed to import document", exc_info=True)
            wx.MessageBox(
                _("Failed to import document. Please try again."),
                _("Error"),
                style=wx.ICON_ERROR
            )
        else:
            sources_updated.send(self, update_sources=True)

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
        issue_import_folder_request(folder, category_name)

    def _on_search_bookshelf(self, provider):
        dialog = SearchBookshelfDialog(
            wx.GetApp().GetTopWindow(),
            _("Search Bookshelf")
        )
        with dialog:
            retval = dialog.ShowModal()
        if retval is None:
            return
        search_query, is_title, is_content = retval
        task = partial(self._do_search_bookshelf, search_query, is_title, is_content)
        AsyncSnakDialog(
            parent=wx.GetApp().GetTopWindow(),
            task=task,
            done_callback=self._search_bookshelf_callback,
            message=_("Searching bookshelf...")
        )

    def _do_search_bookshelf(self, search_query, is_title, is_content):
        title_search_results = (
            ()
            if not is_title
            else tuple(DocumentFTSIndex.search_for_term(search_query, field='title'))
        )
        content_search_results = (
            ()
            if not is_content
            else tuple(DocumentFTSIndex.search_for_term(search_query, field='content'))
        )
        return (title_search_results, content_search_results)

    def _search_bookshelf_callback(self, future):
        try:
            result = future.result()
        except Exception as e:
            log.exception("Failed to search bookshelf", exc_info=True)
            wx.MessageBox(
                _("Failed to search bookshelf,"),
                _("Error"),
                style=wx.ICON_ERROR
            )
        else:
            title_search_results, content_search_results = result
            wx.CallAfter(
                self._show_search_results_dialog,
                title_search_results,
                content_search_results
            )

    def _show_search_results_dialog(self, title_search_results, content_search_results):
        dialog = BookshelfSearchResultsDialog(
            wx.GetApp().GetTopWindow(),
            _("Full Text Search Results"),
            title_search_results=title_search_results,
            content_search_results=content_search_results
        )
        with dialog:
            dialog.ShowModal()

    def _on_bundle_documents(self, provider):
        retval = wx.MessageBox(
            _("This will create copies of all of the documents you have added to your Local Bookshelf.\nAfter this operation, you can open documents stored in your bookshelf, even if you have deleted or moved the original documents.\n\nPlease note that this action will create duplicate copies of all of your added documents."),
            _("Bundle Documents?"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION
        )
        if retval != wx.YES:
            return
        AsyncSnakDialog(
            task=self._do_bundle_documents,
            message=_("Bundling documents. Please wait..."),
            done_callback=self._done_bundling_callback,
            parent=wx.GetApp().GetTopWindow(),
        )

    def _do_bundle_documents(self):
        num_documents = Document.select().count()
        num_succesfull = 0
        func = partial(bundle_single_document, DEFAULT_BOOKSHELF_DATABASE_FILE)
        errors = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            for (idx, (is_ok, src_file, doc_title)) in enumerate(executor.map(func, Document.select())):
                if not is_ok:
                    errors.append((src_file, doc_title))
                num_succesfull += (1 * is_ok)
        return num_documents, num_succesfull, errors

    def _done_bundling_callback(self, future):
        try:
            result = future.result()
        except:
            log.exception("Error bundling documents", exc_info=True)
            return
        num_documents, num_succesfull, errors = result
        if not errors:
            wx.MessageBox(
                _("Bundled {num_documents} files.").format(num_documents=num_documents),
                _("Done"),
                style=wx.ICON_INFORMATION
            )
        else:
            num_faild = num_documents - num_succesfull
            dialog = BundleErrorsDialog(
                None,
                _("Bundle Results: {num_succesfull} successfull, {num_faild} faild").format(num_succesfull=num_succesfull, num_faild=num_faild),
                info=errors
            )
            with dialog:
                dialog.ShowModal()

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
    can_rename_items = True

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
        doc_instance = self.get_doc_instance(item)
        retval = [
            BookshelfAction(
                _("&Edit reading list / collections..."),
                func=lambda doc_info: self._do_edit_category_and_tags(doc_instance)
            ),
            BookshelfAction(
                _("Remove from &currently reading") if doc_instance.is_currently_reading else _("Add to &currently reading"),
                func=partial(self._toggle_togglable_attribute, doc_instance, 'is_currently_reading')
            ),
            BookshelfAction(
                _("Remove from &want to read") if doc_instance.in_reading_list else _("Add to &want to read"),
                func=partial(self._toggle_togglable_attribute, doc_instance, 'in_reading_list')
            ),
            BookshelfAction(
                _("Remove from &favorites") if doc_instance.favorited else _("Add to &favorites"),
                func=partial(self._toggle_togglable_attribute, doc_instance, 'favorited')
            ),
            BookshelfAction(
                _("&Remove from bookshelf"),
                func=lambda doc_info: self._do_remove_from_bookshelf(doc_instance)
            ),
        ]
        return retval

    def change_item_title(self, item, new_title):
        doc_instance = self.get_doc_instance(item)
        doc_instance.title = new_title
        doc_instance.metadata['title'] = new_title
        doc_instance.save()

    def get_doc_instance(self, item):
        return Document.get(item.data['database_id'])

    def _toggle_togglable_attribute(self, doc_instance, attribute, *__doc_info):
        setattr(
            doc_instance,
            attribute,
            not getattr(doc_instance, attribute)
        )
        doc_instance.save()
        sources_updated.send(self.provider, update_items=True)

    def _do_edit_category_and_tags(self, doc_instance):
        top_frame = wx.GetApp().GetTopWindow()
        dialog = EditDocumentClassificationDialog(
            top_frame,
            title=_("Edit reading list/collections"),
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
        unknown_author_query = (
            Document.select()
            .join(
                DocumentAuthor,
                on=DocumentAuthor.document_id == Document.id,
                join_type=peewee.JOIN.LEFT_OUTER
            )
            .where(DocumentAuthor.document_id == None)
            .order_by(Document.title.asc())
        )
        return [
            InvalidIfEmptyLocalDatabaseSource(
                provider=self.provider,
                name=item.name,
                query=Author.get_documents(item.name).order_by(Document.title.asc()),
                model=Author,
            )
            for item in Author.get_all()
        ] + [
            InvalidIfEmptyLocalDatabaseSource(
                provider=self.provider,
                name=_("Unknown Author"),
                query=unknown_author_query,
                model=Author,
            )
        ]


class InvalidIfEmptyLocalDatabaseSource(LocalDatabaseSource):

    def is_valid(self):
        return self.get_item_count() != 0
