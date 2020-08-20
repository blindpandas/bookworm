# coding: utf-8

import System
import time
import sys
import os
import wx
import webbrowser
from operator import ge, le
from pathlib import Path
from chemical import it
from slugify import slugify
from bookworm import config
from bookworm import paths
from bookworm import app
from bookworm.i18n import is_rtl
from bookworm.document_formats import DocumentCapability as DC
from bookworm.signals import config_updated, reader_book_loaded, reader_book_unloaded
from bookworm.otau import check_for_updates
from bookworm.concurrency import call_threaded, process_worker
from bookworm import ocr
from bookworm.otau import check_for_updates
from bookworm.concurrency import call_threaded
from bookworm import speech
from bookworm.reader import EBookReader
from bookworm.utils import restart_application, cached_property, gui_thread_safe
from bookworm.logger import logger
from bookworm.gui.settings import PreferencesDialog
from bookworm.gui.book_viewer.core_dialogs import (
    GoToPageDialog,
    SearchBookDialog,
    SearchResultsDialog,
)
from .render_view import ViewPageAsImageDialog
from .menu_constants import *


log = logger.getChild(__name__)
# Translators: the content of the about message
ABOUT_APPLICATION = _(
    "{display_name}\n"
    "Version: {version}\n"
    "Website: {website}\n\n"
    "{display_name} is an accessible e-book reader that enables blind and visually impaired individuals "
    "to read e-books in an easy, accessible, and hassle-free manor. "
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
        if "after_loading_book" in self.__dict__:
            reader_book_loaded.connect(self.after_loading_book, sender=self.reader)
        if "after_unloading_book" in self.__dict__:
            reader_book_unloaded.connect(self.after_unloading_book, sender=self.reader)


class FileMenu(BaseMenu):
    """The file menu for the book viewer."""

    def create(self):
        # A submenu for recent files
        self.recentFilesMenu = wx.Menu()
        # File menu
        # Translators: the label of an item in the application menubar
        self.Append(wx.ID_OPEN, _("Open...\tCtrl-O"))
        self.AppendSeparator()
        # Translators: the label of an item in the application menubar
        self.Append(BookRelatedMenuIds.export, _("&Save As Plain Text..."))
        self.AppendSeparator()
        self.Append(
            BookRelatedMenuIds.closeCurrentFile,
            # Translators: the label of an item in the application menubar
            _("&Close Current Book\tCtrl-W"),
            # Translators: the help text of an item in the application menubar
            _("Close the currently open e-book"),
        )
        self.AppendSeparator()
        self.AppendSubMenu(
            self.recentFilesMenu,
            # Translators: the label of an item in the application menubar
            _("&Recent Books"),
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
            wx.EVT_MENU, self.onExportAsPlainText, id=BookRelatedMenuIds.export
        )
        self.view.Bind(
            wx.EVT_MENU, self.onCloseCurrentFile, id=BookRelatedMenuIds.closeCurrentFile
        )
        self.view.Bind(wx.EVT_MENU, self.onClearRecentFileList, id=wx.ID_CLEAR)
        self.view.Bind(wx.EVT_MENU, self.onPreferences, id=wx.ID_PREFERENCES)
        self.view.Bind(wx.EVT_MENU, lambda e: self.view.onClose(e), id=wx.ID_EXIT)
        self.view.Bind(wx.EVT_CLOSE, lambda e: self.view.onClose(e), self.view)
        # Populate the recent files submenu
        self._recent_files_data = []
        self.populate_recent_file_list()

    def onOpenEBook(self, event):
        last_folder = config.conf["history"]["last_folder"]
        if not os.path.isdir(last_folder):
            last_folder = str(Path.home())
        openFileDlg = wx.FileDialog(
            self.view,
            # Translators: the title of a file dialog to browse to an e-book
            message=_("Choose an e-book"),
            defaultDir=last_folder,
            wildcard=self.view._get_ebooks_wildcards(),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if openFileDlg.ShowModal() == wx.ID_OK:
            self.view.unloadCurrentEbook()
            filename = openFileDlg.GetPath().strip()
            openFileDlg.Destroy()
            if filename:
                self.view.open_file(filename)
                self.populate_recent_file_list()
                config.conf["history"]["last_folder"] = os.path.split(filename)[0]
                config.save()

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
        dlg = wx.ProgressDialog(
            # Translators: the title of a dialog showing
            # the progress of book export process
            _("Exporting Book"),
            # Translators: the message of a dialog showing the progress of book export
            _("Converting your book to plain text."),
            parent=self.view,
            maximum=total,
            style=wx.PD_APP_MODAL | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE,
        )
        process = self.reader.document.export_to_text(filename)
        self._continue_with_export_to_text(process, dlg, total)

    @call_threaded
    def _continue_with_export_to_text(self, process, progress_dlg, total):
        for progress in process:
            # Translators: a message shown when the book is being exported
            wx.CallAfter(
                progress_dlg.Update,
                progress,
                _("Exporting Page {} of {}...").format(progress + 1, total),
            )
        wx.CallAfter(progress_dlg.Close)
        wx.CallAfter(progress_dlg.Destroy)

    def onRecentFileItem(self, event):
        clicked_id = event.GetId()
        info = [item for item in self._recent_files_data if item[1] == clicked_id][-1]
        filename = info[2]
        if self.reader.ready and (filename == self.reader.document.filename):
            return
        self.view.open_file(filename)
        self.populate_recent_file_list()

    def onClearRecentFileList(self, event):
        config.conf["history"]["recently_opened"] = []
        config.save()
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
        self.populate_recent_file_list()

    def populate_recent_file_list(self):
        clear_item = self.recentFilesMenu.FindItemById(wx.ID_CLEAR)
        for item, _nop, filename in self._recent_files_data:
            self.recentFilesMenu.Delete(item)
        self._recent_files_data.clear()
        recent_files = config.conf["history"]["recently_opened"]
        if len(recent_files) == 0:
            _no_files = self.recentFilesMenu.Append(
                wx.ID_ANY,
                # Translators: the label of an item in the application menubar
                _("(No recent books)"),
                _("No recent books"),
            )
            _no_files.Enable(False)
            self._recent_files_data.append((_no_files, -1, ""))
            clear_item.Enable(False)
        else:
            recent_files = (file for file in recent_files if os.path.exists(file))
            clear_item.Enable(bool(recent_files))
            for idx, filename in enumerate(recent_files):
                fname = os.path.split(filename)[-1]
                item = self.recentFilesMenu.Append(wx.ID_ANY, f"{idx + 1}. {fname}")
                self.view.Bind(wx.EVT_MENU, self.onRecentFileItem, item)
                self._recent_files_data.append((item, item.GetId(), filename))
                if self.reader.ready:
                    for (it, id, fn) in self._recent_files_data:
                        if fn == self.reader.document.filename:
                            it.Enable(False)


class SearchMenu(BaseMenu):
    """The search menu for the book viewer."""

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
        # Bind events
        self.view.Bind(wx.EVT_MENU, self.onGoToPage, id=BookRelatedMenuIds.goToPage)
        self.view.Bind(wx.EVT_MENU, self.onFind, id=wx.ID_FIND)
        self.view.Bind(wx.EVT_MENU, self.onFindNext, id=BookRelatedMenuIds.findNext)
        self.view.Bind(wx.EVT_MENU, self.onFindPrev, id=BookRelatedMenuIds.findPrev)
        self._reset_search_history()

    def after_unloading_book(self, sender):
        self._reset_search_history()

    def onGoToPage(self, event):
        # Translators: the title of the go to page dialog
        with GoToPageDialog(parent=self.view, title=_("Go To Page")) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                retval = dlg.GetValue()
                self.reader.go_to_page(retval)

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
        self._reset_search_history()
        self._recent_search_term = term
        # Translators: the initial title of the search results dialog
        # shown when the search process is not done yet
        dlg = SearchResultsDialog(
            self.highlight_search_result,
            (request.to_page - request.to_page) or 1,
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
            dlg.updateProgress(i + 1)
            it(resultset).for_each(lambda res: dlg.addResult(res)).go()
        if dlg.IsShown():
            # Translators: the final title of the search results dialog
            # shown after the search is finished
            msg = _("Results | {total}").format(total=len(results))
            dlg.SetTitle(msg)
            speech.announce(msg, True)
        self._latest_search_results = tuple(results)

    def go_to_search_result(self, foreword=True):
        result = None
        page, (sol, eol) = self.reader.current_page, self.view.get_selection_range()
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
            return wx.Bell()
        self.highlight_search_result(result.page, result.position)

    def onFindNext(self, event):
        self.go_to_search_result(foreword=True)

    def onFindPrev(self, event):
        self.go_to_search_result(foreword=False)

    def _reset_search_history(self):
        self._latest_search_results = ()
        self._last_search_index = 0
        self._recent_search_term = ""

    @gui_thread_safe
    def highlight_search_result(self, page_number, pos):
        self.reader.go_to_page(page_number)
        start, end = self.view.get_containing_line(pos)
        self.view.select_text(start, end)


class ToolsMenu(BaseMenu):
    """The tools menu for the book viewer."""

    def create(self):
        # Tools menu
        self.renderItem = self.Append(
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

    def after_loading_book(self, sender):
        self.renderItem.Enable(
            DC.GRAPHICAL_RENDERING in self.reader.document.capabilities
        )

    def onViewRenderedAsImage(self, event):
        # Translators: the title of the render page dialog
        with ViewPageAsImageDialog(
            self.view, _("Rendered Page"), style=wx.CLOSE_BOX
        ) as dlg:
            dlg.Maximize()
            dlg.ShowModal()


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
        self.Append(
            ViewerMenuIds.check_for_updates,
            # Translators: the label of an item in the application menubar
            _("&Check for updates"),
            # Translators: the help text of an item in the application menubar
            _("Update the application"),
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
        self.view.Bind(
            wx.EVT_MENU,
            lambda e: check_for_updates(verbose=True),
            id=ViewerMenuIds.check_for_updates,
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
        help_filename = f"bookworm.{'html' if app.is_frozen else 'md'}"
        lang = app.current_language.given_lang
        docs = paths.docs_path(lang, help_filename)
        wx.LaunchDefaultApplication(str(docs))


class MenubarProvider:
    """The application menubar."""

    def __init__(self):
        self.menuBar = wx.MenuBar()
        # Context menu
        self.contentTextCtrl.Bind(
            self.contentTextCtrl.EVT_CONTEXTMENU_REQUESTED,
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
        k_shourtcuts = KEYBOARD_SHORTCUTS.copy()
        k_shourtcuts.update(wx.GetApp().service_handler.get_keyboard_shourtcuts())
        for menu_id, shortcut in k_shourtcuts.items():
            accel = wx.AcceleratorEntry(cmd=menu_id)
            accel.FromString(shortcut)
            entries.append(accel)
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def onClose(self, evt):
        self.unloadCurrentEbook()
        self.Destroy()
        evt.Skip()

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
            (
                30,
                _("&Render Page...\tCtrl-R"),
                _("View a fully rendered version of this page."),
                BookRelatedMenuIds.viewRenderedAsImage,
            ),
        ]
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
        for cls in EBookReader.document_classes:
            for ext in cls.extensions:
                rv.append("{name} ({ext})|{ext}|".format(name=_(cls.name), ext=ext))
                all_exts.append(ext)
        rv[-1] = rv[-1].rstrip("|")
        allfiles = ";".join(all_exts)
        allfiles_display = " ".join(e for e in all_exts)
        rv.insert(
            0,
            _("Supported E-Book Formats ({display})|{ext}|").format(
                display=allfiles_display, ext=allfiles
            ),
        )
        return "".join(rv)
