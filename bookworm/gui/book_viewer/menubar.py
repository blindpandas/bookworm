# coding: utf-8

import inspect
import os
import shutil
import sys
import threading
import webbrowser
from contextlib import suppress
from functools import partial
from operator import ge, le
from pathlib import Path

import more_itertools
import wx
from slugify import slugify

from bookworm import app, config, ocr, paths, speech
from bookworm.commandline_handler import run_subcommand_in_a_new_process
from bookworm.concurrency import call_threaded, process_worker
from bookworm.document import READING_MODE_LABELS
from bookworm.document import DocumentCapability as DC
from bookworm.document import DocumentInfo, PaginationError
from bookworm.document.uri import DocumentUri
from bookworm.gui.book_viewer.core_dialogs import (
    DocumentInfoDialog,
    ElementListDialog,
    GoToPageDialog,
    SearchBookDialog,
    SearchResultsDialog,
)
from bookworm.gui.components import AsyncSnakDialog, RobustProgressDialog
from bookworm.gui.contentview_ctrl import EVT_CONTEXTMENU_REQUESTED
from bookworm.gui.settings import PreferencesDialog
from bookworm.i18n import is_rtl
from bookworm.logger import logger
from bookworm.reader import EBookReader
from bookworm.resources import sounds
from bookworm.signals import (
    config_updated,
    reader_book_loaded,
    reader_book_unloaded,
    reading_position_change,
)
from bookworm.utils import gui_thread_safe, restart_application

from . import recents_manager
from .menu_constants import *
from .render_view import ViewPageAsImageDialog

log = logger.getChild(__name__)
# Translators: the content of the about message
ABOUT_APPLICATION = _(
    "{display_name}\n"
    "Version: {version}\n"
    "Website: {website}\n\n"
    "{display_name} is an advanced and accessible document reader that enables blind and visually impaired individuals "
    "to read documents in an easy, accessible, and hassle-free manor. "
    "It is being developed by {author} with some contributions from the community.\n\n"
    "{copyright}\n"
    "{display_name} is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.\n"
    "This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n"
    "For further details, you can view the full licence from the help menu.\n"
)
EXTRA_ABOUT_MESSAGE = _(
    "This release of Bookworm is generously sponsored  by Capeds (www.capeds.net)."
)


class BaseMenu(wx.Menu):
    def __init__(self, view, reader, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view = view
        self.reader = reader
        self.create()


class FileMenu(BaseMenu):
    """The file menu for the book viewer."""

    def __init__(self, *args, **kwargs):
        self._recents = {}
        self._pinned = {}
        super().__init__(*args, **kwargs)
        self.view.add_load_handler(self.after_loading_book)
        reader_book_unloaded.connect(self.after_unloading_book, sender=self.reader)

    def create(self):
        # A submenu for pinned documents
        self.pinnedDocumentsMenu = wx.Menu()
        # A submenu for recent documents
        self.recentFilesMenu = wx.Menu()
        # File menu
        # Translators: the label of an item in the application menubar
        self.Append(wx.ID_OPEN, _("Open...\tCtrl-O"))
        # Translators: the label of an item in the application menubar
        self.Append(wx.ID_NEW, _("New Window...\tCtrl-N"))
        self.AppendSeparator()
        # Translators: the label of an item in the application menubar
        self.Append(
            BookRelatedMenuIds.pin_document, _("&Pin\tCtrl-P"), kind=wx.ITEM_CHECK
        )
        # Translators: the label of an item in the application menubar
        self.Append(BookRelatedMenuIds.export, _("&Save As Plain Text..."))
        self.AppendSeparator()
        self.Append(
            BookRelatedMenuIds.closeCurrentFile,
            # Translators: the label of an item in the application menubar
            _("&Close Current Document\tCtrl-W"),
            # Translators: the help text of an item in the application menubar
            _("Close the currently open document"),
        )
        self.AppendSeparator()
        self.Append(
            ViewerMenuIds.clear_documents_cache,
            # Translators: the label of an item in the application menubar
            _("C&lear Documents Cache..."),
            # Translators: the help text of an item in the application menubar
            _(
                "Clear the document cache. Helps in fixing some issues with openning documents."
            ),
        )
        self.AppendSeparator()
        self.AppendSubMenu(
            self.pinnedDocumentsMenu,
            # Translators: the label of an item in the application menubar
            _("Pi&nned Documents"),
            # Translators: the help text of an item in the application menubar
            _("Opens a list of documents you pinned."),
        )
        self.clearPinnedDocumentsID = wx.NewIdRef()
        self.pinnedDocumentsMenu.Append(
            self.clearPinnedDocumentsID,
            # Translators: the label of an item in the application menubar
            _("Clear list"),
            # Translators: the help text of an item in the application menubar
            _("Clear the pinned documents list"),
        )
        self.AppendSubMenu(
            self.recentFilesMenu,
            # Translators: the label of an item in the application menubar
            _("&Recently Opened"),
            # Translators: the help text of an item in the application menubar
            _("Opens a list of recently opened books."),
        )
        self.recentFilesMenu.Append(
            wx.ID_CLEAR,
            # Translators: the label of an item in the application menubar
            _("Clear list"),
            # Translators: the help text of an item in the application menubar
            _("Clear the recent books list."),
        )
        self.AppendSeparator()
        self.Append(
            wx.ID_PREFERENCES,
            # Translators: the label of an item in the application menubar
            _("&Preferences...\tCtrl-Shift-P"),
            # Translators: the help text of an item in the application menubar
            _("Configure application"),
        )
        self.AppendSeparator()
        # Translators: the label of an item in the application menubar
        self.Append(wx.ID_EXIT, _("Exit"))
        # Bind event handlers
        self.view.Bind(wx.EVT_MENU, self.onOpenEBook, id=wx.ID_OPEN)
        self.view.Bind(wx.EVT_MENU, self.onNewWindow, id=wx.ID_NEW)
        self.view.Bind(
            wx.EVT_MENU, self.onClearPinDocuments, id=self.clearPinnedDocumentsID
        )
        self.view.Bind(
            wx.EVT_MENU, self.onPinDocument, id=BookRelatedMenuIds.pin_document
        )
        self.view.Bind(
            wx.EVT_MENU, self.onExportAsPlainText, id=BookRelatedMenuIds.export
        )
        self.view.Bind(
            wx.EVT_MENU, self.onCloseCurrentFile, id=BookRelatedMenuIds.closeCurrentFile
        )
        self.view.Bind(
            wx.EVT_MENU,
            self.onClearDocumentCache,
            id=ViewerMenuIds.clear_documents_cache,
        )
        self.view.Bind(wx.EVT_MENU, self.onClearRecentFileList, id=wx.ID_CLEAR)
        self.view.Bind(wx.EVT_MENU, self.onPreferences, id=wx.ID_PREFERENCES)
        self.view.Bind(wx.EVT_MENU, lambda e: self.view.onClose(e), id=wx.ID_EXIT)
        self.view.Bind(wx.EVT_CLOSE, lambda e: self.view.onClose(e), self.view)
        # Populate the submenues
        self.populate_pinned_documents_list()
        self.populate_recent_file_list()

    def after_loading_book(self, sender):
        doc = sender.document
        if doc.uri.view_args.get("allow_pinning", True):
            self.Check(BookRelatedMenuIds.pin_document, recents_manager.is_pinned(doc))
            self.populate_pinned_documents_list()
        else:
            self.Enable(BookRelatedMenuIds.pin_document, False)
        if doc.uri.view_args.get("add_to_recents", True):
            recents_manager.add_to_recents(doc)
            self.populate_recent_file_list()

    def after_unloading_book(self, sender):
        self.populate_pinned_documents_list()
        self.populate_recent_file_list()

    def onOpenEBook(self, event):
        last_folder = config.conf["history"]["last_folder"]
        if not os.path.isdir(last_folder):
            last_folder = str(Path.home())
        openFileDlg = wx.FileDialog(
            self.view,
            # Translators: the title of a file dialog to browse to a document
            message=_("Select a document"),
            defaultDir=last_folder,
            wildcard=self.view._get_ebooks_wildcards(),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if openFileDlg.ShowModal() == wx.ID_OK:
            self.view.unloadCurrentEbook()
            filename = openFileDlg.GetPath().strip()
            openFileDlg.Destroy()
            if filename:
                config.conf["history"]["last_folder"] = os.path.split(filename)[0]
                config.save()
                self.view.open_uri(DocumentUri.from_filename(filename))

    def onNewWindow(self, event):
        args = []
        if app.debug:
            args.append("--debug")
        run_subcommand_in_a_new_process(args, hidden=False)

    def onClearPinDocuments(self, event):
        recents_manager.clear_pinned()
        self.populate_pinned_documents_list()
        self.Check(BookRelatedMenuIds.pin_document, False)

    def onPinDocument(self, event):
        if self.IsChecked(event.GetId()):
            recents_manager.pin(self.reader.document)
            sounds.pinning.play()
            speech.announce("Pinned")
        else:
            recents_manager.unpin(self.reader.document)
            sounds.pinning.play()
            speech.announce("Unpinned")
        self.populate_pinned_documents_list()

    def onExportAsPlainText(self, event):
        book_title = slugify(self.reader.current_book.title)
        filename, _nope = wx.FileSelectorEx(
            # Translators: the title of a dialog to save the exported book
            _("Save As"),
            default_path=wx.GetUserHome(),
            default_filename=f"{book_title}.txt",
            # Translators: a name of a file format
            wildcard=_("Plain Text") + " (*.txt)|.txt",
            flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            parent=self.view,
        )
        if not filename.strip():
            return
        if self.reader.document.is_single_page_document():
            with open(filename, "w", encoding="utf-8") as file:
                file.write(self.reader.document.get_content())
            return
        total = len(self.reader.document)
        dlg = RobustProgressDialog(
            self.view,
            # Translators: the title of a dialog showing
            # the progress of book export process
            _("Exporting Document"),
            # Translators: the message of a dialog showing the progress of book export
            _("Converting document to plain text."),
            maxvalue=total,
            can_hide=True,
            can_abort=True,
        )
        process = self.reader.document.export_to_text(filename)
        if inspect.isgenerator(process):
            dlg.set_abort_callback(process.close)
        else:
            dlg.set_abort_callback(process.cancel)
        self._continue_with_export_to_text(process, dlg, total)

    @call_threaded
    def _continue_with_export_to_text(self, process, progress_dlg, total):
        for progress in process:
            progress_dlg.Update(
                progress,
                # Translators: a message shown when the book is being exported
                _("Exporting Page {current} of {total}...").format(
                    current=progress + 1, total=total
                ),
            )
        progress_dlg.Dismiss()

    def onDocumentReferenceClicked(self, item_to_doc_map, event):
        item_id = event.GetId()
        item_uri = item_to_doc_map[item_id]
        if self.reader.ready and (item_uri == self.reader.document.uri):
            return
        item_uri.view_args["from_list"] = True
        self.view.open_uri(item_uri)

    def onClearRecentFileList(self, event):
        recents_manager.clear_recents()
        self.populate_recent_file_list()

    def onPreferences(self, event):
        dlg = PreferencesDialog(
            self.view,
            # Translators: the title of the application preferences dialog
            title=_("{app_name} Preferences").format(app_name=app.display_name),
        )
        with dlg:
            dlg.ShowModal()

    def onCloseCurrentFile(self, event):
        self.view.unloadCurrentEbook()

    def onClearDocumentCache(self, event):
        retval = wx.MessageBox(
            # Translators: content of a message
            _("Are you sure you want to clear the documents cache?"),
            # Translators: title of a message box
            _("Clear Documents Cache?"),
            style=wx.YES_NO | wx.ICON_WARNING,
        )
        if retval != wx.YES:
            return
        task = partial(shutil.rmtree, paths.home_data_path(), ignore_errors=True)
        done_callback = lambda fut: wx.MessageBox(
            # Translators: content of a message box
            _("Documents cache has been cleared."),
            # Translators: title of a message box
            _("Success"),
            style=wx.ICON_INFORMATION,
        )
        AsyncSnakDialog(
            task=task,
            done_callback=done_callback,
            # Translators: content of a message in a message box
            message=_("Clearing documents cache..."),
            parent=self.view,
        )

    def populate_pinned_documents_list(self):
        clear_item = self.pinnedDocumentsMenu.FindItemById(self.clearPinnedDocumentsID)
        for mitem in (
            i for i in self.pinnedDocumentsMenu.GetMenuItems() if i != clear_item
        ):
            self.pinnedDocumentsMenu.Delete(mitem)
        self._pinned.clear()
        pinned = recents_manager.get_pinned()
        if not len(pinned):
            clear_item.Enable(False)
            return
        else:
            clear_item.Enable(True)
        for idx, pinned_item in enumerate(pinned):
            item = self.pinnedDocumentsMenu.Append(
                wx.ID_ANY, f"{idx + 1}. {pinned_item.title}"
            )
            self.view.Bind(
                wx.EVT_MENU,
                partial(self.onDocumentReferenceClicked, self._pinned),
                item,
            )
            self._pinned[item.Id] = pinned_item.uri
        if self.reader.ready:
            current_document = self.reader.document
            for (item_id, uri) in self._pinned.items():
                if uri == current_document.uri:
                    self.pinnedDocumentsMenu.Enable(item_id, False)

    def populate_recent_file_list(self):
        clear_item = self.recentFilesMenu.FindItemById(wx.ID_CLEAR)
        self._recents.clear()
        for mitem in self.recentFilesMenu.GetMenuItems():
            if mitem != clear_item:
                self.recentFilesMenu.Delete(mitem)
        recents = recents_manager.get_recents()
        if len(recents) == 0:
            _no_files = self.recentFilesMenu.Append(
                wx.ID_ANY,
                # Translators: the label of an item in the application menubar
                _("(No recent books)"),
                _("No recent books"),
            )
            _no_files.Enable(False)
            clear_item.Enable(False)
        else:
            clear_item.Enable(True)
            recent_uris = {}
            for idx, recent_item in enumerate(recents):
                item = self.recentFilesMenu.Append(
                    wx.ID_ANY, f"{idx + 1}. {recent_item.title}"
                )
                self.view.Bind(
                    wx.EVT_MENU,
                    partial(self.onDocumentReferenceClicked, self._recents),
                    item,
                )
                self._recents[item.Id] = recent_item.uri
                recent_uris[recent_item.uri] = item.Id
            if (
                self.reader.ready
                and (current_uri := self.reader.document.uri) in recent_uris
            ):
                item_id = recent_uris[current_uri]
                self.recentFilesMenu.Enable(item_id, False)


class DocumentMenu(BaseMenu):
    """Actions related to the current document."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view.add_load_handler(self.after_loading_book)

    def create(self):
        self.Append(
            BookRelatedMenuIds.document_info,
            # Translators: the label of an item in the application menubar
            _("Document &Info..."),
            # Translators: the help text of an item in the application menubar
            _("Show information about number of chapters, word count..etc."),
        )
        self.Append(
            BookRelatedMenuIds.element_list,
            # Translators: the label of an item in the application menubar
            _("&Element list...\tCtrl+F7"),
            # Translators: the help text of an item in the application menubar
            _("Show a list of semantic elements."),
        )
        self.Append(
            BookRelatedMenuIds.changeReadingMode,
            # Translators: the label of an item in the application menubar
            _("Change Reading &Mode...\tCtrl-Shift-M"),
            # Translators: the help text of an item in the application menubar
            _("Change the current reading mode."),
        )
        self.Append(
            BookRelatedMenuIds.viewRenderedAsImage,
            # Translators: the label of an item in the application menubar
            _("&Render Page...\tCtrl-R"),
            # Translators: the help text of an item in the application menubar
            _("View a fully rendered version of this page."),
        )
        # Bind event handlers
        self.view.Bind(
            wx.EVT_MENU,
            self.onViewRenderedAsImage,
            id=BookRelatedMenuIds.viewRenderedAsImage,
        )
        self.view.Bind(
            wx.EVT_MENU,
            self.onChangeReadingMode,
            id=BookRelatedMenuIds.changeReadingMode,
        )
        self.view.Bind(
            wx.EVT_MENU, self.onElementList, id=BookRelatedMenuIds.element_list
        )
        self.view.Bind(
            wx.EVT_MENU, self.onDocumentInfo, id=BookRelatedMenuIds.document_info
        )

    def after_loading_book(self, sender):
        ctrl_enable_info = (
            (
                BookRelatedMenuIds.element_list,
                self.reader.document.supports_structural_navigation(),
            ),
            (
                BookRelatedMenuIds.viewRenderedAsImage,
                self.reader.document.can_render_pages(),
            ),
            (
                BookRelatedMenuIds.changeReadingMode,
                len(self.reader.document.supported_reading_modes) > 1,
            ),
        )
        for ctrl_id, enable in ctrl_enable_info:
            self.Enable(ctrl_id, enable)
            self.view.toolbar.EnableTool(ctrl_id, enable)

    def onViewRenderedAsImage(self, event):
        # Translators: the title of the render page dialog
        with ViewPageAsImageDialog(
            self.view, _("Rendered Page"), style=wx.CLOSE_BOX
        ) as dlg:
            dlg.Maximize()
            dlg.ShowModal()

    def _after_reading_mode_changed(self, most_recent_page):
        with suppress(PaginationError):
            self.reader.go_to_page(most_recent_page)

    def onChangeReadingMode(self, event):
        current_reading_mode = self.reader.document.reading_options.reading_mode
        supported_reading_modes = self.reader.document.supported_reading_modes
        supported_reading_modes_display = [
            _(READING_MODE_LABELS[redmo]) for redmo in supported_reading_modes
        ]
        dlg = wx.SingleChoiceDialog(
            self.view,
            _("Available reading modes"),
            _("Select Reading Mode "),
            supported_reading_modes_display,
            wx.CHOICEDLG_STYLE,
        )
        dlg.SetSelection(supported_reading_modes.index(current_reading_mode))
        if dlg.ShowModal() == wx.ID_OK:
            uri = self.reader.document.uri.create_copy()
            new_reading_mode = supported_reading_modes[dlg.GetSelection()]
            if current_reading_mode != new_reading_mode:
                uri.openner_args["reading_mode"] = int(new_reading_mode)
                most_recent_page = self.reader.current_page
                self.view.open_uri(
                    uri,
                    callback=partial(
                        self._after_reading_mode_changed, most_recent_page
                    ),
                )
        dlg.Destroy()

    def onElementList(self, event):
        dlg = ElementListDialog(
            self.view, title=_("Element List"), view=self.view, reader=self.reader
        )
        with dlg:
            if (selected_element_info := dlg.ShowModal()) is not None:
                self.view.go_to_position(*selected_element_info.text_range)

    def onDocumentInfo(self, event):
        document_info = DocumentInfo.from_document(self.reader.document)
        with DocumentInfoDialog(
            self.view, view=self.view, document_info=document_info
        ) as dlg:
            dlg.ShowModal()


class SearchMenu(BaseMenu):
    """The search menu for the book viewer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view.add_load_handler(self.after_loading_book)
        self.search_lock = threading.RLock()
        reader_book_unloaded.connect(self.after_unloading_book, sender=self.reader)

    def create(self):
        self.Append(
            wx.ID_FIND,
            # Translators: the label of an item in the application menubar
            _("&Find in Document...\tCtrl-F"),
            # Translators: the help text of an item in the application menubar
            _("Search this document."),
        )
        self.Append(
            BookRelatedMenuIds.findNext,
            # Translators: the label of an item in the application menubar
            _("&Find &Next\tF3"),
            # Translators: the help text of an item in the application menubar
            _("Find next occurrence."),
        )
        self.Append(
            BookRelatedMenuIds.findPrev,
            # Translators: the label of an item in the application menubar
            _("&Find &Previous\tShift-F3"),
            # Translators: the help text of an item in the application menubar
            _("Find previous occurrence."),
        )
        self.Append(
            BookRelatedMenuIds.goToLine,
            # Translators: the label of an item in the application menubar
            _("&Go To Line...\tCtrl-L"),
            # Translators: the help text of an item in the application menubar
            _("Go to a line within the current page"),
        )
        self.Append(
            BookRelatedMenuIds.goToPage,
            # Translators: the label of an item in the application menubar
            _("&Go To Page...\tCtrl-G"),
            # Translators: the help text of an item in the application menubar
            _("Go to page"),
        )
        self.Append(
            BookRelatedMenuIds.goToPageByLabel,
            # Translators: the label of an item in the application menubar
            _("&Go To Page By Label...\tCtrl-Shift-G"),
            # Translators: the help text of an item in the application menubar
            _("Go to a page using its label"),
        )
        # Bind events
        self.view.Bind(wx.EVT_MENU, self.onGoToPage, id=BookRelatedMenuIds.goToPage)
        self.view.Bind(wx.EVT_MENU, self.onGoToLine, id=BookRelatedMenuIds.goToLine)
        self.view.Bind(
            wx.EVT_MENU, self.onGoToPageByLabel, id=BookRelatedMenuIds.goToPageByLabel
        )
        self.view.Bind(wx.EVT_MENU, self.onFind, id=wx.ID_FIND)
        self.view.Bind(wx.EVT_MENU, self.onFindNext, id=BookRelatedMenuIds.findNext)
        self.view.Bind(wx.EVT_MENU, self.onFindPrev, id=BookRelatedMenuIds.findPrev)
        self._reset_search_history()

    def after_loading_book(self, sender):
        self.maintain_state(False)
        is_single_page_doc = self.reader.document.is_single_page_document()
        self.Enable(BookRelatedMenuIds.goToPage, not is_single_page_doc)
        self.view.toolbar.EnableTool(
            BookRelatedMenuIds.goToPage, not is_single_page_doc
        )

    def after_unloading_book(self, sender):
        self._reset_search_history()

    def onGoToLine(self, event):
        textCtrl = self.view.contentTextCtrl
        if (idx_last_line := self.view.get_line_number(textCtrl.GetLastPosition())) == 0:
            return wx.Bell()
        last_line = idx_last_line + 1
        current_line = self.view.get_line_number(self.view.get_insertion_point()) + 1
        target_line = wx.GetNumberFromUser(
            _("You are here: {current_line}\nYou can't go further than: {last_line}").format(current_line=current_line, last_line=last_line),
            _("Line number"),
            _("Jump to line"),
            value=current_line,
            min=1,
            max=last_line
        )
        insertion_point = self.view.get_start_of_line(target_line - 1)
        textCtrl.SetFocus()
        self.view.set_insertion_point(insertion_point)

    def onGoToPage(self, event):
        # Translators: the title of the go to page dialog
        with GoToPageDialog(parent=self.view, title=_("Go To Page")) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                retval = dlg.GetValue()
                self.reader.go_to_page(retval)

    def onGoToPageByLabel(self, event):
        page_label = self.view.get_text_from_user(
            _("Go To Page By Label"), _("Page Label")
        )
        if page_label is not None:
            if (navigated := self.reader.go_to_page_by_label(page_label)) is False:
                wx.Bell()

    def onFind(self, event):
        # Translators: the title of the search dialog
        dlg = SearchBookDialog(parent=self.view, title=_("Search Document"))
        if dlg.ShowModal() != wx.ID_OK:
            return
        request = dlg.GetValue()
        term = request.term
        dlg.Destroy()
        del dlg
        if not term:
            return
        last_searches = config.conf["history"]["recent_terms"]
        if len(last_searches) > 9:
            config.conf["history"]["recent_terms"] = last_searches[:9]
        config.conf["history"]["recent_terms"].insert(0, term)
        config.save()
        self.maintain_state(False)
        self._reset_search_history()
        self._recent_search_term = term
        with self.search_lock:
            self._last_search_request = request
        num_pages = (request.to_page - request.from_page) or 1
        # Translators: the initial title of the search results dialog
        # shown when the search process is not done yet
        dlg = SearchResultsDialog(
            self.highlight_search_result,
            num_pages,
            self.view,
            title=_("Searching For '{term}'").format(term=term),
        )
        dlg.Show()
        self._add_search_results(request, dlg)

    @call_threaded
    def _add_search_results(self, request, dlg):
        search_func = self.reader.document.search
        results = []
        for (i, resultset) in enumerate(search_func(request)):
            results.extend(resultset)
            if dlg.IsShown():
                dlg.addResultSet(resultset)
        # Translators: message to announce the number of search results
        # also used as the final title of the search results dialog
        msg = _("Results | {total}").format(total=len(results))
        with self.search_lock:
            if self._last_search_request != request:
                return
            speech.announce(msg, True)
            sounds.ready.play()
            if dlg.IsShown():
                dlg.SetTitle(msg)
            self._latest_search_results = tuple(results)
            self.maintain_state(True)

    def go_to_search_result(self, foreword=True):
        result = None
        page, (sol, eol) = self.reader.current_page, self.view.get_containing_line(
            self.view.get_insertion_point()
        )
        if foreword:
            filter_func = lambda sr: (
                ((sr.page == page) and (sr.position > eol)) or (sr.page > page)
            )
        else:
            filter_func = lambda sr: (
                ((sr.page == page) and (sr.position < sol)) or (sr.page < page)
            )
        result_iter = filter(filter_func, self._latest_search_results)
        try:
            if foreword:
                result = more_itertools.first(result_iter)
            else:
                result = more_itertools.last(result_iter)
        except ValueError:
            sounds.navigation.play()
        else:
            self.highlight_search_result(result.page, result.position)
            reading_position_change.send(
                self.view,
                position=result.position,
                tts_speech_prefix=_("Search Result"),
            )

    def onFindNext(self, event):
        self.go_to_search_result(foreword=True)

    def onFindPrev(self, event):
        self.go_to_search_result(foreword=False)

    def _reset_search_history(self):
        self._latest_search_results = ()
        self._last_search_index = 0
        self._recent_search_term = ""
        self._last_search_request = None

    @gui_thread_safe
    def maintain_state(self, enable):
        self.Enable(
            BookRelatedMenuIds.goToPageByLabel,
            DC.PAGE_LABELS in self.reader.document.capabilities,
        )
        for item_id in {BookRelatedMenuIds.findNext, BookRelatedMenuIds.findPrev}:
            self.Enable(item_id, enable)

    @gui_thread_safe
    def highlight_search_result(self, page_number, pos):
        self.reader.go_to_page(page_number)
        start, end = self.view.get_containing_line(pos)
        self.view.select_text(start, end)


class HelpMenu(BaseMenu):
    """The application help menu."""

    def create(self):
        self.Append(
            ViewerMenuIds.documentation,
            # Translators: the label of an item in the application menubar
            _("&User guide...\tF1"),
            # Translators: the help text of an item in the application menubar
            _("View Bookworm manuals"),
        )
        self.Append(
            ViewerMenuIds.website,
            # Translators: the label of an item in the application menubar
            _("Bookworm &website..."),
            # Translators: the help text of an item in the application menubar
            _("Visit the official website of Bookworm"),
        )
        self.Append(
            ViewerMenuIds.license,
            # Translators: the label of an item in the application menubar
            _("&License"),
            # Translators: the help text of an item in the application menubar
            _("View legal information about this program ."),
        )
        self.Append(
            ViewerMenuIds.contributors,
            # Translators: the label of an item in the application menubar
            _("Con&tributors"),
            # Translators: the help text of an item in the application menubar
            _("View a list of notable contributors to the program."),
        )
        if app.is_frozen and not app.debug:
            self.Append(
                ViewerMenuIds.restart_with_debug,
                # Translators: the label of an item in the application menubar
                _("&Restart with debug-mode enabled"),
                # Translators: the help text of an item in the application menubar
                _("Restart the program with debug mode enabled to show errors"),
            )
            self.view.Bind(
                wx.EVT_MENU,
                self.onRestartWithDebugMode,
                id=ViewerMenuIds.restart_with_debug,
            )
        self.Append(
            ViewerMenuIds.about,
            # Translators: the label of an item in the application menubar
            _("&About Bookworm") + "...",
            # Translators: the help text of an item in the application menubar
            _("Show general information about this program"),
        )
        # Bind menu events
        self.view.Bind(
            wx.EVT_MENU, self.onOpenDocumentation, id=ViewerMenuIds.documentation
        )
        self.view.Bind(
            wx.EVT_MENU,
            lambda e: webbrowser.open(app.website),
            id=ViewerMenuIds.website,
        )
        self.view.Bind(
            wx.EVT_MENU,
            lambda e: wx.LaunchDefaultApplication(
                str(paths.resources_path("license.txt"))
            ),
            id=ViewerMenuIds.license,
        )
        self.view.Bind(
            wx.EVT_MENU,
            lambda e: wx.LaunchDefaultApplication(
                str(paths.resources_path("contributors.txt"))
            ),
            id=ViewerMenuIds.contributors,
        )
        self.view.Bind(wx.EVT_MENU, self.onAbout, id=ViewerMenuIds.about)

    def onAbout(self, event):
        wx.MessageBox(
            "{}\n{}".format(
                _(ABOUT_APPLICATION).format(**app.__dict__), _(EXTRA_ABOUT_MESSAGE)
            ),
            # Translators: the title of the about dialog
            _("About {app_name}").format(app_name=app.display_name),
            parent=self.view,
            style=wx.ICON_INFORMATION,
        )

    def onRestartWithDebugMode(self, event):
        restart_application(debug=True)

    def onOpenDocumentation(self, event):
        userguide_filename = paths.userguide_path(
            app.current_language.pylang, "bookworm.html"
        )
        wx.LaunchDefaultApplication(str(userguide_filename))


class MenubarProvider:
    """The application menubar."""

    def __init__(self):
        self.menuBar = wx.MenuBar()
        # Context menu
        self.contentTextCtrl.Bind(
            EVT_CONTEXTMENU_REQUESTED,
            self.onContentTextCtrlContextMenu,
            self.contentTextCtrl,
        )

        # The menus
        self.fileMenu = FileMenu(self, self.reader)
        self.documentMenu = DocumentMenu(self, self.reader)
        self.searchMenu = SearchMenu(self, self.reader)
        self.helpMenu = HelpMenu(self, self.reader)
        self.__menus = [
            # Translators: the label of an item in the application menubar
            (0, self.fileMenu, _("&File")),
            # Translators: the label of an item in the application menubar
            (5, self.searchMenu, _("&Search")),
            # Translators: the label of an item in the application menubar
            (10, self.documentMenu, _("&Document")),
            # Translators: the label of an item in the application menubar
            (100, self.helpMenu, _("&Help")),
        ]

    def doAddMenus(self):
        self.__menus.sort(key=lambda item: item[0])
        for (__, menu, label) in self.__menus:
            self.menuBar.Append(menu, label)

    def registerMenu(self, order, menu, label):
        self.__menus.append((order, menu, label))

    def _set_menu_accelerators(self):
        entries = []
        k_shortcuts = KEYBOARD_SHORTCUTS.copy()
        k_shortcuts.update(wx.GetApp().service_handler.get_keyboard_shortcuts())
        for menu_id, shortcut in k_shortcuts.items():
            accel = wx.AcceleratorEntry(cmd=menu_id)
            accel.FromString(shortcut)
            entries.append(accel)
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def onClose(self, evt):
        try:
            self.unloadCurrentEbook()
            self.Destroy()
            evt.Skip()
        except:
            log.exception(
                "An unhandled error was occurred while exiting Bookworm", exc_info=True
            )
            wx.Abort()

    def get_content_text_ctrl_context_menu(self):
        menu = wx.Menu()
        entries = [
            (
                10,
                _("&Go To Page...\tCtrl-G"),
                _("Jump to a page"),
                BookRelatedMenuIds.goToPage,
            ),
            (
                20,
                _("&Find in Document...\tCtrl-F"),
                _("Search this document."),
                wx.ID_FIND,
            ),
            (21, "", "", None),
        ]
        if self.reader.ready and self.reader.document.can_render_pages():
            entries.append(
                (
                    30,
                    _("&Render Page...\tCtrl-R"),
                    _("View a fully rendered version of this page."),
                    BookRelatedMenuIds.viewRenderedAsImage,
                ),
            )
        entries.extend(wx.GetApp().service_handler.get_contextmenu_items())
        entries.sort()
        for (__, label, desc, ident) in entries:
            if ident is None:
                menu.AppendSeparator()
                continue
            menu.Append(ident, label, desc)
        return menu

    def onContentTextCtrlContextMenu(self, event):
        pos = self.contentTextCtrl.PositionToCoords(self.contentTextCtrl.InsertionPoint)
        context_menu = self.get_content_text_ctrl_context_menu()
        if not self.reader.ready:
            for item in context_menu.GetMenuItems():
                item.Enable(False)
        self.PopupMenu(context_menu, pos=pos)

    @staticmethod
    def _get_ebooks_wildcards():
        rv = []
        all_exts = []
        visible_doc_cls = [
            doc_cls
            for doc_cls in EBookReader.get_document_format_info().values()
            if not doc_cls.__internal__
        ]
        for cls in visible_doc_cls:
            for ext in cls.extensions:
                rv.append("{name} ({ext})|{ext}|".format(name=_(cls.name), ext=ext))
                all_exts.append(ext)
        rv[-1] = rv[-1].rstrip("|")
        allfiles = ";".join(all_exts)
        allfiles_display = " ".join(e for e in all_exts)
        rv.insert(
            0, _("Supported document formats") + f" ({allfiles_display})|{allfiles}|"
        )
        return "".join(rv)
