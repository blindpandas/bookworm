# coding: utf-8

import sys
import os
import threading
import wx
import webbrowser
from operator import ge, le
from contextlib import suppress
from functools import partial
from pathlib import Path
from chemical import it
from slugify import slugify
from bookworm import config
from bookworm import paths
from bookworm import app
from bookworm.i18n import is_rtl
from bookworm.resources import sounds
from bookworm.document_formats import PaginationError, DocumentCapability as DC
from bookworm.document_formats.base import READING_MODE_LABELS
from bookworm.signals import (
    navigated_to_search_result,
    config_updated,
    reader_book_loaded,
    reader_book_unloaded,
)
from bookworm.concurrency import call_threaded, process_worker
from bookworm.gui.components import RobustProgressDialog
from bookworm import ocr
from bookworm import speech
from bookworm.reader import EBookReader, DocumentUri
from bookworm.utils import restart_application, gui_thread_safe
from bookworm.logger import logger
from bookworm.gui.contentview_ctrl import EVT_CONTEXTMENU_REQUESTED
from bookworm.gui.settings import PreferencesDialog
from bookworm.gui.book_viewer.core_dialogs import (
    GoToPageDialog,
    SearchBookDialog,
    SearchResultsDialog,
)
from .render_view import ViewPageAsImageDialog
from .menu_constants import *
from . import recents_manager


log = logger.getChild(__name__)
# Translators: the content of the about message
ABOUT_APPLICATION = _(
    "{display_name}\n"
    "Version: {version}\n"
    "Website: {website}\n\n"
    "{display_name} is an accessible document reader that enables blind and visually impaired individuals "
    "to read documents in an easy, accessible, and hassle-free manor. "
    "It is being developed by {author} with some contributions from the community.\n\n"
    "{copyright}\n"
    "This software is offered to you under the terms of The MIT license.\n"
    "You can view the license text from the help menu.\n\n"
    "As blind developers, our responsibility is to develop applications that provide independence for "
    "us, and for our fellow blind friends all over the world. So, if you've found Bookworm useful "
    "in any way, please help us in making Bookworm better for you and for others. At this initial "
    "stage, we want you to tell us about any errors you may encounter during your use of Bookworm. "
    "To do so, open a new issue with the details of the error at "
    "the issue tracker (https://github.com/mush42/bookworm/issues/). "
    "Your help is greatly appreciated."
).format(**app.__dict__)


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
        reader_book_loaded.connect(self.after_loading_book)
        reader_book_unloaded.connect(self.after_unloading_book, sender=self.reader)

    def create(self):
        # A submenu for pinned documents
        self.pinnedDocumentsMenu = wx.Menu()
        # A submenu for recent documents
        self.recentFilesMenu = wx.Menu()
        # File menu
        # Translators: the label of an item in the application menubar
        self.Append(wx.ID_OPEN, _("Open...\tCtrl-O"))
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
            _("&Close Current Book\tCtrl-W"),
            # Translators: the help text of an item in the application menubar
            _("Close the currently open document"),
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
        self.view.Bind(wx.EVT_MENU, self.onClearRecentFileList, id=wx.ID_CLEAR)
        self.view.Bind(wx.EVT_MENU, self.onPreferences, id=wx.ID_PREFERENCES)
        self.view.Bind(wx.EVT_MENU, lambda e: self.view.onClose(e), id=wx.ID_EXIT)
        self.view.Bind(wx.EVT_CLOSE, lambda e: self.view.onClose(e), self.view)
        # Populate the submenues
        self.populate_pinned_documents_list()
        self.populate_recent_file_list()

    def after_loading_book(self, sender):
        self.Check(
            BookRelatedMenuIds.pin_document, recents_manager.is_pinned(sender.document)
        )
        self.populate_pinned_documents_list()
        recents_manager.add_to_recents(sender.document)
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
            # Translators: the title of a file dialog to browse to an e-book
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
        total = len(self.reader.document)
        dlg = RobustProgressDialog(
            self.view,
            # Translators: the title of a dialog showing
            # the progress of book export process
            _("Exporting Book"),
            # Translators: the message of a dialog showing the progress of book export
            _("Converting your book to plain text."),
            maxvalue=total,
            can_hide=True,
            can_abort=True,
        )
        process = self.reader.document.export_to_text(filename)
        dlg.set_abort_callback(process.cancel)
        self._continue_with_export_to_text(process, dlg, total)

    @call_threaded
    def _continue_with_export_to_text(self, process, progress_dlg, total):
        for progress in process:
            progress_dlg.Update(
                progress,
                # Translators: a message shown when the book is being exported
                _("Exporting Page {current} of {total}...").format(current=progress + 1, total=total),
            )
        progress_dlg.Dismiss()

    def onDocumentReferenceClicked(self, item_to_doc_map, event):
        item_id = event.GetId()
        item_uri = item_to_doc_map[item_id]
        if self.reader.ready and (item_uri == self.reader.document.uri):
            return
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
            _("&Find in Book...\tCtrl-F"),
            # Translators: the help text of an item in the application menubar
            _("Search this book."),
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
        dlg = SearchBookDialog(parent=self.view, title=_("Search book"))
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
        result_iter = it(self._latest_search_results).filter(filter_func)
        try:
            result = (result_iter if foreword else result_iter.rev()).next()
        except StopIteration:
            sounds.navigation.play()
            return
        self.highlight_search_result(result.page, result.position)
        navigated_to_search_result.send(self.view, position=result.position)

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


class ToolsMenu(BaseMenu):
    """The tools menu for the book viewer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view.add_load_handler(self.after_loading_book)

    def create(self):
        # Tools menu
        self.Append(
            BookRelatedMenuIds.viewRenderedAsImage,
            # Translators: the label of an item in the application menubar
            _("&Render Page...\tCtrl-R"),
            # Translators: the help text of an item in the application menubar
            _("View a fully rendered version of this page."),
        )
        self.Append(
            BookRelatedMenuIds.changeReadingMode,
            # Translators: the label of an item in the application menubar
            _("Change Reading &Mode...\tCtrl-Shift-M"),
            # Translators: the help text of an item in the application menubar
            _("Change the current reading mode."),
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

    def after_loading_book(self, sender):
        ctrl_enable_info = (
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
            lambda e: wx.LaunchDefaultApplication(str(paths.docs_path("license.txt"))),
            id=ViewerMenuIds.license,
        )
        self.view.Bind(
            wx.EVT_MENU,
            lambda e: wx.LaunchDefaultApplication(
                str(paths.docs_path("contributors.txt"))
            ),
            id=ViewerMenuIds.contributors,
        )
        self.view.Bind(wx.EVT_MENU, self.onAbout, id=ViewerMenuIds.about)

    def onAbout(self, event):
        wx.MessageBox(
            _(ABOUT_APPLICATION),
            # Translators: the title of the about dialog
            _("About {app_name}").format(app_name=app.display_name),
            parent=self.view,
            style=wx.ICON_INFORMATION,
        )

    def onRestartWithDebugMode(self, event):
        restart_application(debug=True)

    def onOpenDocumentation(self, event):
        docs = paths.docs_path(app.current_language.pylang, "bookworm.html")
        wx.LaunchDefaultApplication(str(docs))


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
        self.searchMenu = SearchMenu(self, self.reader)
        self.toolsMenu = ToolsMenu(self, self.reader)
        self.helpMenu = HelpMenu(self, self.reader)

        # Translators: the label of an item in the application menubar
        self.menuBar.Append(self.fileMenu, _("&File"))
        # Translators: the label of an item in the application menubar
        self.menuBar.Append(self.searchMenu, _("&Search"))
        # Translators: the label of an item in the application menubar
        self.menuBar.Append(self.toolsMenu, _("&Tools"))
        # Translators: the label of an item in the application menubar
        self.menuBar.Append(self.helpMenu, _("&Help"))

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
            (20, _("&Find in Book...\tCtrl-F"), _("Search this book."), wx.ID_FIND),
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

    def _get_ebooks_wildcards(self):
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
            0,
            _("Supported document formats") + f" ({allfiles_display})|{allfiles}|"
        )
        return "".join(rv)
