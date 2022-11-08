# coding: utf-8

from __future__ import annotations

import math
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property, partial
from pathlib import Path

import peewee
import wx

from bookworm import config
from bookworm.document import DocumentInfo
from bookworm.document.uri import DocumentUri
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.gui.components import AsyncSnakDialog
from bookworm.logger import logger
from bookworm.signals import app_booting

from ..provider import (
    BookshelfAction,
    BookshelfProvider,
    ItemContainerSource,
    MetaSource,
    Source,
    sources_updated,
)
from .dialogs import (
    AddFolderToLocalBookshelfDialog,
    BookshelfSearchResultsDialog,
    BundleErrorsDialog,
    EditDocumentClassificationDialog,
    SearchBookshelfDialog,
)
from .models import (
    DEFAULT_BOOKSHELF_DATABASE_FILE,
    Author,
    BaseModel,
    Category,
    Document,
    DocumentAuthor,
    DocumentFTSIndex,
    DocumentTag,
    Tag,
)
from .tasks import (
    add_document_to_bookshelf,
    bundle_single_document,
    import_folder_to_bookshelf,
)

log = logger.getChild(__name__)


@app_booting.connect
def create_db_tables(sender):
    BaseModel.create_all()


class LocalBookshelfProvider(BookshelfProvider):

    name = "local_bookshelf"
    # Translators: the name of a book shelf type.
    # This bookshelf type is stored in a local database
    display_name = _("Local Bookshelf")

    @classmethod
    def check(cls) -> bool:
        return True

    def _create_local_database_sources_from_model(self, model):
        remove_source_action = BookshelfAction(
            # Translators: the label of a menu item to remove a bookshelf reading list or collection
            _("Remove..."),
            func=self._on_remove_source,
        )
        change_name_action = BookshelfAction(
            # Translators: the label of a menu item to change the name of a bookshelf reading list or collection
            _("Edit name..."),
            func=self._on_change_name,
        )
        remove_related_documents_action = BookshelfAction(
            # Translators: the label of a menu item to remove all documents under a specific bookshelf reading list or collection
            _("Clear documents..."),
            func=self._on_remove_related_documents,
            decider=lambda source: source.get_item_count() > 0,
        )
        return [
            LocalDatabaseSource(
                provider=self,
                name=item.name,
                query=model.get_documents(item.name),
                model=model,
                source_actions=[
                    change_name_action,
                    remove_related_documents_action,
                    remove_source_action,
                ],
            )
            for item in model.get_all()
        ]

    def get_sources(self):
        sources = [
            LocalDatabaseSource(
                provider=self,
                # Translators: the name of a category in the bookshelf for recently added documents
                name=_("Recently Added"),
                query=Document.select().order_by(Document.date_added.desc()).limit(10),
                source_actions=[],
            ),
            LocalDatabaseSource(
                provider=self,
                # Translators: the name of a category in the bookshelf for documents currently being read by the user
                name=_("Currently Reading"),
                query=Document.select()
                .where(Document.is_currently_reading == True)
                .order_by(Document.title.asc()),
                source_actions=[],
            ),
            LocalDatabaseSource(
                provider=self,
                # Translators: the name of a category in the bookshelf for documents the user wants to read
                name=_("Want to Read"),
                query=Document.select()
                .where(Document.in_reading_list == True)
                .order_by(Document.title.asc()),
                source_actions=[],
            ),
            LocalDatabaseSource(
                provider=self,
                # Translators: the name of a category in the bookshelf for documents favored by the user
                name=_("Favorites"),
                query=Document.select()
                .where(Document.favorited == True)
                .order_by(Document.title.asc()),
                source_actions=[],
            ),
        ]
        classifications = [
            (
                # Translators: the name of a category in the bookshelf which contains the user's reading lists
                _("Reading Lists"),
                (self._create_local_database_sources_from_model(Category), Category),
            ),
            (
                # Translators: the name of a category in the bookshelf which contains the user's collections
                _("Collections"),
                (self._create_local_database_sources_from_model(Tag), Tag),
            ),
        ]
        classifications[0][1][0].append(
            InvalidIfEmptyLocalDatabaseSource(
                provider=self,
                # Translators: the name of a reading list in the bookshelf which contains documents that do not have any category assigned to them
                name=_("General"),
                query=Document.select()
                .where(Document.category == None)
                .order_by(Document.title.asc()),
                source_actions=[],
            ),
        )
        add_new_action = BookshelfAction(
            # Translators: the label of a menu item in the bookshelf to add a new reading list or collection
            _("Add New..."),
            func=self._on_add_new,
        )
        sources += [
            MetaSource(
                provider=self,
                name=name,
                sources=srcs,
                source_actions=[
                    add_new_action,
                ],
                data={"model": model},
            )
            for (name, (srcs, model)) in classifications
        ]
        sources += [
            AuthorMetaSource(
                provider=self,
                # Translators: the name of a category in the bookshelf that lists the authors of the documents stored in the bookshelf
                name=_("Authors"),
                data={"model": Author},
                sources=None,
            )
        ]
        return sources

    def get_provider_actions(self):
        return [
            BookshelfAction(
                # Translators: the label of a menu item in the bookshelf file menu to import documents to the bookshelf
                _("Import Documents...\tCtrl+O"),
                func=self._on_import_document,
            ),
            BookshelfAction(
                # Translators: the label of a menu item in the bookshelf file menu to import an entire folder to the bookshelf
                _("Import documents from folder..."),
                func=self._on_add_documents_from_folder,
            ),
            # Translators: the label of a menu item in the bookshelf file menu to search documents contained in the bookshelf
            BookshelfAction(_("Search Bookshelf..."), func=self._on_search_bookshelf),
            # Translators: the label of a menu item in the bookshelf file menu to copy the files added to the bookshelf to a private folder that blongs to Bookworm.
            # This is important to make the bookshelf works with  portable copies, or if the user wants to move or rename added documents
            BookshelfAction(_("Bundle Documents..."), func=self._on_bundle_documents),
            BookshelfAction(
                # Translators: the label of a menu item in the bookshelf file menu to clear documents that no longer exist in the file system
                _("Clear invalid documents..."),
                func=self._on_clear_invalid_documents,
            ),
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
            filename for filename in openFileDlg.GetPaths() if os.path.isfile(filename)
        ]
        openFileDlg.Destroy()
        if not filenames:
            return
        dialog = EditDocumentClassificationDialog(
            wx.GetApp().GetTopWindow(),
            # Translators: the title of a dialog to edit the document's reading list or collection
            title=_("Edit reading list/collections"),
            categories=[cat.name for cat in Category.get_all()],
        )
        with dialog:
            if (retval := dialog.ShowModal()) is not None:
                category_name, tags_names, should_add_to_fts = retval
            else:
                return
        task = partial(
            self._do_add_files_to_bookshelf,
            filenames,
            category_name=category_name,
            tags_names=tags_names,
            should_add_to_fts=should_add_to_fts,
        )
        message = (
            # Translators: a message shown when Bookworm is importing documents to the bookshelf
            _("Importing document...")
            if len(filenames) == 1
            # Translators: a message shown when Bookworm is importing documents to the bookshelf
            else _("Importing documents...")
        )
        AsyncSnakDialog(
            task=task,
            done_callback=self._on_document_imported_callback,
            message=message,
            parent=wx.GetApp().GetTopWindow(),
        )

    def _do_add_files_to_bookshelf(
        self, filenames, category_name, tags_names, should_add_to_fts
    ):
        for filename in filenames:
            add_document_to_bookshelf(
                DocumentUri.from_filename(filename),
                category_name=category_name,
                tags_names=tags_names,
                should_add_to_fts=should_add_to_fts,
                database_file=DEFAULT_BOOKSHELF_DATABASE_FILE,
            )

    def _on_document_imported_callback(self, future):
        try:
            future.result()
        except Exception as e:
            log.exception("Failed to import document", exc_info=True)
            wx.MessageBox(
                # Translators: content of a message shown when importing documents to the bookshelf has failed
                _("Failed to import document. Please try again."),
                # Translators: title of a message shown when importing documents to the bookshelf has failed
                _("Error"),
                style=wx.ICON_ERROR,
            )
        else:
            sources_updated.send(self, update_sources=True)

    def _on_add_documents_from_folder(self, provider):
        top_frame = wx.GetApp().GetTopWindow()
        dialog = AddFolderToLocalBookshelfDialog(
            top_frame,
            # Translators: title of a dialog to import an entire folder to the bookshelf
            _("Import Documents From Folder"),
        )
        with dialog:
            retval = dialog.ShowModal()
        if retval is None:
            return
        folder, category_name, should_add_to_fts = retval
        task = partial(
            import_folder_to_bookshelf, folder, category_name, should_add_to_fts
        )
        AsyncSnakDialog(
            task=task,
            done_callback=self._on_folder_import_done,
            # Translators: a message shown when importing an entire folder to the bookshelf
            message=_("Importing documents from folder. Please wait..."),
            parent=wx.GetApp().GetTopWindow(),
        )

    def _on_folder_import_done(self, future):
        try:
            future.result()
            wx.MessageBox(
                # Translators: content of a message shown when importing documents from a folder to the bookshelf is successful
                _("Documents imported from folder."),
                # Translators: title of a message shown when importing documents from a folder to the bookshelf is successful
                _("Operation Completed"),
                style=wx.ICON_INFORMATION,
            )
            sources_updated.send(self, update_sources=True)
        except Exception:
            log.exception("Failed to import folder", exc_info=True)
            wx.MessageBox(
                # Translators: content of a message shown when importing documents from a folder to the bookshelf has failed
                _("Failed to import documents from folder."),
                # Translators: title  of a message shown when importing documents from a folder to the bookshelf has failed
                _("Error"),
                style=wx.ICON_ERROR,
            )

    def _on_search_bookshelf(self, provider):
        dialog = SearchBookshelfDialog(
            wx.GetApp().GetTopWindow(),
            # Translators: title of a dialog to search bookshelf
            _("Search Bookshelf"),
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
            # Translators: a message shown while searching bookshelf
            message=_("Searching bookshelf..."),
        )

    def _do_search_bookshelf(self, search_query, is_title, is_content):
        title_search_results = (
            ()
            if not is_title
            else tuple(DocumentFTSIndex.search_for_term(search_query, field="title"))
        )
        content_search_results = (
            ()
            if not is_content
            else tuple(DocumentFTSIndex.search_for_term(search_query, field="content"))
        )
        return (title_search_results, content_search_results)

    def _search_bookshelf_callback(self, future):
        try:
            result = future.result()
        except Exception as e:
            log.exception("Failed to search bookshelf", exc_info=True)
            wx.MessageBox(
                # Translators: content of a message shown when searching bookshelf has failed
                _("Failed to search bookshelf,"),
                # Translators: title of a message shown when searching bookshelf has failed
                _("Error"),
                style=wx.ICON_ERROR,
            )
        else:
            title_search_results, content_search_results = result
            wx.CallAfter(
                self._show_search_results_dialog,
                title_search_results,
                content_search_results,
            )

    def _show_search_results_dialog(self, title_search_results, content_search_results):
        dialog = BookshelfSearchResultsDialog(
            wx.GetApp().GetTopWindow(),
            # Translators: title of a dialog that shows bookshelf search results. It searches documents by title and content, hence full-text
            _("Full Text Search Results"),
            title_search_results=title_search_results,
            content_search_results=content_search_results,
        )
        with dialog:
            dialog.ShowModal()

    def _on_bundle_documents(self, provider):
        retval = wx.MessageBox(
            # Translators: content of a message to confirm the bundling of documents added to bookshelf
            _(
                "This will create copies of all of the documents you have added to your Local Bookshelf.\nAfter this operation, you can open documents stored in your bookshelf, even if you have deleted or moved the original documents.\n\nPlease note that this action will create duplicate copies of all of your added documents."
            ),
            # Translators: title of a message to confirm the bundling of documents added to bookshelf
            _("Bundle Documents?"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION,
        )
        if retval != wx.YES:
            return
        AsyncSnakDialog(
            task=self._do_bundle_documents,
            # Translators: a message shown when bundling documents added to bookshelf
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
            for (idx, (is_ok, src_file, doc_title)) in enumerate(
                executor.map(func, Document.select())
            ):
                if not is_ok:
                    errors.append((src_file, doc_title))
                num_succesfull += 1 * is_ok
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
                # Translators: content of a message when bundling of documents is successful
                _("Bundled {num_documents} files.").format(num_documents=num_documents),
                # Translators: title of a message when bundling of documents is successful
                _("Done"),
                style=wx.ICON_INFORMATION,
            )
        else:
            num_faild = num_documents - num_succesfull
            dialog = BundleErrorsDialog(
                None,
                # Translators: title of a dialog that shows titles and paths of documents which have not been bundled successfully
                _(
                    "Bundle Results: {num_succesfull} successfull, {num_faild} faild"
                ).format(num_succesfull=num_succesfull, num_faild=num_faild),
                info=errors,
            )
            with dialog:
                dialog.ShowModal()

    def _on_clear_invalid_documents(self, provider):
        retval = wx.MessageBox(
            # Translators: content of a message to confirm the clearing of documents
            # which have been added to bookshelf, but they have been moved, renamed, or deleted
            _(
                "This action will clear invalid documents from your bookshelf.\nInvalid documents are the documents which no longer exist on your computer."
            ),
            # Translators: title of a message to confirm the clearing of documents
            # which have been added to bookshelf, but they have been moved, renamed, or deleted
            _("Clear Invalid Documents?"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION,
        )
        if retval != wx.YES:
            return
        for doc in Document.select():
            if not os.path.isfile(doc.uri.path):
                doc.delete_instance()
        sources_updated.send(self, update_items=True)

    def _on_change_name(self, source):
        instance = source.model.get(name=source.name)
        old_name = instance.name
        new_name = wx.GetTextFromUser(
            # Translators: label of a text box to change the name of a reading list or collection
            _("New name:"),
            # Translators: title of a dialog to change the name of a reading list or collection
            _("Edit Name"),
            default_value=old_name,
        ).strip()
        if new_name and (new_name != old_name):
            instance.name = new_name
            try:
                instance.save()
            except peewee.IntegrityError:
                wx.MessageBox(
                    # Translators: content of a message when changing the name of a reading list or collection was not successful
                    _(
                        "The given name {name} already exists.\nPlease choose another name."
                    ).format(name=new_name),
                    # Translators: title of a message when changing the name of a reading list or collection was not successful
                    _("Duplicate name"),
                    style=wx.ICON_WARNING,
                )
                self._on_change_name(source)
            else:
                sources_updated.send(self, update_sources=True)

    def _on_remove_source(self, source):
        retval = wx.MessageBox(
            # Translators: content of a message to confirm the removal of a reading list or collection
            _(
                "Are you sure you want to remove {name}?\nThis will not remove document classified under {name}."
            ).format(name=source.name),
            # Translators: title of a message to confirm the removal of a reading list or collection
            _("Confirm"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION,
        )
        if retval == wx.YES:
            instance = source.model.get(name=source.name)
            source.model.delete_instance(instance)
            sources_updated.send(self, update_sources=True)

    def _on_remove_related_documents(self, source):
        retval = wx.MessageBox(
            # Translators: content of a message to confirm the removal of all documents classified under a specific reading list or collection
            _(
                "Are you sure you want to clear all documents classified under {name}?\nThis will remove those documents from your bookshelf."
            ).format(name=source.name),
            # Translators: title of a message to confirm the removal of all documents classified under a specific reading list or collection
            _("Clear All Documents"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION,
        )
        if retval == wx.YES:
            for item in source:
                Document.delete().where(
                    Document.id == item.data["database_id"]
                ).execute()
            sources_updated.send(self, update_items=True)

    def _on_add_new(self, source):
        new_name = wx.GetTextFromUser(
            # Translators: label of a text box for the name of a new reading list or collection
            _("Enter name:"),
            # Translators: title of a dialog  for adding a new reading list or collection
            _("Add New"),
        )
        source.data["model"].get_or_create(name=new_name)
        sources_updated.send(self, update_sources=True)


class LocalDatabaseSource(Source):
    can_rename_items = True

    def __init__(self, query, *args, model=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.model = model

    def get_items(self):
        return [doc.as_document_info() for doc in self.query.clone()]

    def get_item_count(self):
        return self.query.count()

    def get_item_actions(self, item):
        doc_instance = self.get_doc_instance(item)
        retval = [
            BookshelfAction(
                # Translators: label of an item in the context menu of a document in the bookshelf
                _("&Edit reading list / collections..."),
                func=lambda doc_info: self._do_edit_category_and_tags(doc_instance),
            ),
            BookshelfAction(
                # Translators: label of an item in the context menu of a document in the bookshelf
                _("Remove from &currently reading") if doc_instance.is_currently_reading
                # Translators: label of an item in the context menu of a document in the bookshelf
                else _("Add to &currently reading"),
                func=lambda __: self._do_toggle_currently_reading(doc_instance),
            ),
            BookshelfAction(
                # Translators: label of an item in the context menu of a document in the bookshelf
                _("Remove from &want to read") if doc_instance.in_reading_list
                # Translators: label of an item in the context menu of a document in the bookshelf
                else _("Add to &want to read"),
                func=lambda __: self._do_toggle_in_reading_list(doc_instance),
            ),
            BookshelfAction(
                # Translators: label of an item in the context menu of a document in the bookshelf
                _("Remove from &favorites") if doc_instance.favorited
                # Translators: label of an item in the context menu of a document in the bookshelf
                else _("Add to &favorites"),
                func=lambda __: self._do_toggle_favorited(doc_instance),
            ),
            BookshelfAction(
                # Translators: label of an item in the context menu of a document in the bookshelf
                _("&Remove from bookshelf"),
                func=lambda doc_info: self._do_remove_from_bookshelf(doc_instance),
            ),
        ]
        return retval

    def change_item_title(self, item, new_title):
        doc_instance = self.get_doc_instance(item)
        doc_instance.title = new_title
        doc_instance.metadata["title"] = new_title
        doc_instance.save()

    def get_doc_instance(self, item):
        return Document.get(item.data["database_id"])

    def _do_toggle_favorited(self, doc_instance):
        doc_instance.favorited = not doc_instance.favorited
        doc_instance.save()
        sources_updated.send(self.provider, update_items=True)

    def _do_toggle_currently_reading(self, doc_instance):
        doc_instance.is_currently_reading = not doc_instance.is_currently_reading
        if doc_instance.is_currently_reading:
            doc_instance.in_reading_list = False
        doc_instance.save()
        sources_updated.send(self.provider, update_items=True)

    def _do_toggle_in_reading_list(self, doc_instance):
        doc_instance.in_reading_list = not doc_instance.in_reading_list
        if doc_instance.in_reading_list:
            doc_instance.is_currently_reading = False
        doc_instance.save()
        sources_updated.send(self.provider, update_items=True)

    def _do_edit_category_and_tags(self, doc_instance):
        top_frame = wx.GetApp().GetTopWindow()
        dialog = EditDocumentClassificationDialog(
            top_frame,
            # Translators: title of a dialog to change the reading list or collection for a document
            title=_("Edit reading list/collections"),
            categories=[cat.name for cat in Category.get_all()],
            given_category=None
            if not doc_instance.category
            else doc_instance.category.name,
            tags_names=[
                Tag.get_by_id(doc_tag.tag_id).name
                for doc_tag in DocumentTag.select().where(
                    DocumentTag.document_id == doc_instance.get_id()
                )
            ],
            can_fts_index=False,
        )
        with dialog:
            if (retval := dialog.ShowModal()) is None:
                return
            category_name, tags_names, should_add_to_fts = retval
            anything_created = doc_instance.change_category_and_tags(
                category_name, tags_names
            )
            sources_updated.send(
                self.provider, update_sources=anything_created, update_items=True
            )

    def _do_remove_from_bookshelf(self, doc_instance):
        retval = wx.MessageBox(
            # Translators: content of a message to confirm the removal of this document from bookshelf
            _(
                "Are you sure you want to remove this document from your bookshelf?\nTitle: {title}\nThis will remove the document from all tags and categories."
            ).format(title=doc_instance.title),
            # Translators: title of a message to confirm the removal of this document from bookshelf
            _("Remove From Bookshelf?"),
            style=wx.YES_NO | wx.ICON_EXCLAMATION,
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
                join_type=peewee.JOIN.LEFT_OUTER,
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
                # Translators: the name of a category under the Authors category. This category shows documents for which  author info is not available
                name=_("Unknown Author"),
                query=unknown_author_query,
                model=Author,
            )
        ]


class InvalidIfEmptyLocalDatabaseSource(LocalDatabaseSource):
    def is_valid(self):
        return self.get_item_count() != 0
