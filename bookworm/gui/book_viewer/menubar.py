# coding: utf-8

import time
import sys
import os
import wx
import webbrowser
from pathlib import Path
from slugify import slugify
from bookworm import config
from bookworm import paths
from bookworm import app
from bookworm.otau import check_for_updates
from bookworm.concurrency import call_threaded
from bookworm import speech
from bookworm.reader import EBookReader
from bookworm.utils import restart_application, cached_property, gui_thread_safe
from bookworm.logger import logger
from bookworm.gui.settings import PreferencesDialog
from bookworm.gui.book_viewer.decorators import only_when_reader_ready
from bookworm.gui.book_viewer.core_dialogs import (
    GoToPageDialog,
    SearchBookDialog,
    SearchResultsDialog,
    ViewPageAsImageDialog,
)
from ._menu_constants import *


log = logger.getChild(__name__)


class MenubarProvider:
    """The application menubar."""

    def __init__(self):
        self.menuBar = wx.MenuBar()
        self._reset_search_history()

        # The menu
        self.fileMenu = fileMenu = wx.Menu()
        self.toolsMenu = toolsMenu = wx.Menu()
        self.helpMenu = helpMenu = wx.Menu()
        # A submenu for recent files
        self.recentFilesMenu = wx.Menu()

        # add items to the menu
        # File menu
        # Translators: the label of an ietm in the application menubar
        fileMenu.Append(wx.ID_OPEN, _("Open...\tCtrl-O"))
        fileMenu.AppendSeparator()
        # Translators: the label of an ietm in the application menubar
        fileMenu.Append(BookRelatedMenuIds.export, _("&Save As Plain Text..."))
        fileMenu.AppendSeparator()
        fileMenu.Append(
            BookRelatedMenuIds.closeCurrentFile,
            # Translators: the label of an ietm in the application menubar
            _("&Close Current Book\tCtrl-W"),
            # Translators: the help text of an ietm in the application menubar
            _("Close the currently open e-book"),
        )
        fileMenu.AppendSeparator()
        fileMenu.AppendSubMenu(
            self.recentFilesMenu,
            # Translators: the label of an ietm in the application menubar
            _("&Recent Books"),
            # Translators: the help text of an ietm in the application menubar
            _("Opens a list of recently opened books."),
        )
        self.recentFilesMenu.Append(
            wx.ID_CLEAR,
            # Translators: the label of an ietm in the application menubar
            _("Clear list"),
            # Translators: the help text of an ietm in the application menubar
            _("Clear the recent books list."),
        )
        fileMenu.AppendSeparator()
        # Translators: the label of an ietm in the application menubar
        fileMenu.Append(wx.ID_EXIT, _("Exit"))
        # Tools menu
        toolsMenu.Append(
            BookRelatedMenuIds.goToPage,
            # Translators: the label of an ietm in the application menubar
            _("&Go To Page...\tCtrl-G"),
            # Translators: the help text of an ietm in the application menubar
            _("Go to page"),
        )
        toolsMenu.Append(
            wx.ID_FIND,
            # Translators: the label of an ietm in the application menubar
            _("&Find in Book...\tCtrl-F"),
            # Translators: the help text of an ietm in the application menubar
            _("Search this book."),
        )
        toolsMenu.Append(
            BookRelatedMenuIds.findNext,
            # Translators: the label of an ietm in the application menubar
            _("&Find &Next\tF3"),
            # Translators: the help text of an ietm in the application menubar
            _("Find next occurrence."),
        )
        toolsMenu.Append(
            BookRelatedMenuIds.findPrev,
            # Translators: the label of an ietm in the application menubar
            _("&Find &Previous\tShift-F3"),
            # Translators: the help text of an ietm in the application menubar
            _("Find previous occurrence."),
        )
        self.renderItem = toolsMenu.Append(
            BookRelatedMenuIds.viewRenderedAsImage,
            # Translators: the label of an ietm in the application menubar
            _("&Render Page...\tCtrl-R"),
            # Translators: the help text of an ietm in the application menubar
            _("View a fully rendered version of this page."),
        )
        toolsMenu.Append(
            wx.ID_PREFERENCES,
            # Translators: the label of an ietm in the application menubar
            _("&Preferences...\tCtrl-Shift-P"),
            # Translators: the help text of an ietm in the application menubar
            _("Configure application"),
        )
        # Help menu
        helpMenu.Append(
            ViewerMenuIds.documentation,
            # Translators: the label of an ietm in the application menubar
            _("&User guide...\tF1"),
            # Translators: the help text of an ietm in the application menubar
            _("View Bookworm manuals"),
        )
        helpMenu.Append(
            ViewerMenuIds.website,
            # Translators: the label of an ietm in the application menubar
            _("Bookworm &website..."),
            # Translators: the help text of an ietm in the application menubar
            _("Visit the official website of Bookworm"),
        )
        helpMenu.Append(
            ViewerMenuIds.license,
            # Translators: the label of an ietm in the application menubar
            _("&License"),
            # Translators: the help text of an ietm in the application menubar
            _("View legal information about this program ."),
        )
        helpMenu.Append(
            ViewerMenuIds.contributors,
            # Translators: the label of an ietm in the application menubar
            _("Con&tributors"),
            # Translators: the help text of an ietm in the application menubar
            _("View a list of notable contributors to the program."),
        )
        helpMenu.Append(
            ViewerMenuIds.check_for_updates,
            # Translators: the label of an ietm in the application menubar
            _("&Check for updates"),
            # Translators: the help text of an ietm in the application menubar
            _("Update the application"),
        )
        if app.is_frozen and not app.debug:
            helpMenu.Append(
                ViewerMenuIds.restart_with_debug,
                # Translators: the label of an ietm in the application menubar
                _("&Restart with debug-mode enabled"),
                # Translators: the help text of an ietm in the application menubar
                _("Restart the program with debug mode enabled to show errors"),
            )
            self.Bind(
                wx.EVT_MENU,
                self.onRestartWithDebugMode,
                id=ViewerMenuIds.restart_with_debug,
            )
        helpMenu.Append(
            ViewerMenuIds.about,
            # Translators: the label of an ietm in the application menubar
            _("&About Bookworm") + "...",
            # Translators: the help text of an ietm in the application menubar
            _("Show general information about this program"),
        )

        # Bind menu events to event handlers
        # File menu event handlers
        self.Bind(wx.EVT_MENU, self.onOpenEBook, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.onExportAsPlainText, id=BookRelatedMenuIds.export)
        self.Bind(
            wx.EVT_MENU, self.onCloseCurrentFile, id=BookRelatedMenuIds.closeCurrentFile
        )
        self.Bind(wx.EVT_MENU, self.onClearRecentFileList, id=wx.ID_CLEAR)
        self.Bind(wx.EVT_MENU, self.onClose, id=wx.ID_EXIT)
        self.Bind(wx.EVT_CLOSE, self.onClose, self)

        # Tools menu event handlers
        self.Bind(wx.EVT_MENU, self.onGoToPage, id=BookRelatedMenuIds.goToPage)
        self.Bind(wx.EVT_MENU, self.onFind, id=wx.ID_FIND)
        self.Bind(wx.EVT_MENU, self.onFindNext, id=BookRelatedMenuIds.findNext)
        self.Bind(wx.EVT_MENU, self.onFindPrev, id=BookRelatedMenuIds.findPrev)
        self.Bind(
            wx.EVT_MENU,
            self.onViewRenderedAsImage,
            id=BookRelatedMenuIds.viewRenderedAsImage,
        )
        self.Bind(wx.EVT_MENU, self.onPreferences, id=wx.ID_PREFERENCES)

        # Help menu event handlers
        self.Bind(wx.EVT_MENU, self.onOpenDocumentation, id=ViewerMenuIds.documentation)
        self.Bind(
            wx.EVT_MENU,
            lambda e: webbrowser.open(app.website),
            id=ViewerMenuIds.website,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: wx.LaunchDefaultApplication(str(paths.docs_path("license.txt"))),
            id=ViewerMenuIds.license,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: wx.LaunchDefaultApplication(
                str(paths.docs_path("contributors.txt"))
            ),
            id=ViewerMenuIds.contributors,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: check_for_updates(verbose=True),
            id=ViewerMenuIds.check_for_updates,
        )
        self.Bind(wx.EVT_MENU, self.onAbout, id=ViewerMenuIds.about)

        # and put the menu on the menubar
        # Translators: the label of an ietm in the application menubar
        self.menuBar.Append(fileMenu, _("&File"))
        # Translators: the label of an ietm in the application menubar
        self.menuBar.Append(toolsMenu, _("&Tools"))
        # Translators: the label of an ietm in the application menubar
        self.menuBar.Append(helpMenu, _("&Help"))

        # Populate the recent files submenu
        self._recent_files_data = []
        self.populate_recent_file_list()

    def _set_menu_accelerators(self):
        entries = []
        k_shourtcuts = KEYBOARD_SHORTCUTS.copy()
        k_shourtcuts.update(wx.GetApp().service_handler.get_keyboard_shourtcuts())
        for menu_id, shortcut in k_shourtcuts.items():
            accel = wx.AcceleratorEntry(cmd=menu_id)
            accel.FromString(shortcut)
            entries.append(accel)
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def onOpenEBook(self, event):
        last_folder = config.conf["history"]["last_folder"]
        if not os.path.isdir(last_folder):
            last_folder = str(Path.home())
        openFileDlg = wx.FileDialog(
            self,
            # Translators: the title of a file dialog to browse to an e-book
            message=_("Choose an e-book"),
            defaultDir=last_folder,
            wildcard=self._get_ebooks_wildcards(),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if openFileDlg.ShowModal() == wx.ID_OK:
            self.unloadCurrentEbook()
            filename = openFileDlg.GetPath().strip()
            openFileDlg.Destroy()
            if filename:
                self.open_file(filename)
                config.conf["history"]["last_folder"] = os.path.split(filename)[0]
                config.save()

    @call_threaded
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
            parent=self,
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
            parent=self,
            maximum=total - 1,
            style=wx.PD_APP_MODAL | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE,
        )
        export_func = self.reader.document.export_to_text
        for progress in export_func(self.reader.document.filename, filename):
            # Translators: a message shown when the book is being exported
            dlg.Update(progress, _("Converting book..."))
        dlg.Close()
        dlg.Destroy()

    def onRecentFileItem(self, event):
        clicked_id = event.GetId()
        info = [item for item in self._recent_files_data if item[1] == clicked_id][-1]
        filename = info[2]
        if self.reader.ready and (filename == self.reader.document.filename):
            return
        self.open_file(filename)

    def onClearRecentFileList(self, event):
        config.conf["history"]["recently_opened"] = []
        config.save()
        self.populate_recent_file_list()

    def onClose(self, evt):
        self.unloadCurrentEbook()
        self.Destroy()
        evt.Skip()

    @only_when_reader_ready
    def onCloseCurrentFile(self, event):
        self.unloadCurrentEbook()
        self.populate_recent_file_list()

    @only_when_reader_ready
    def onGoToPage(self, event):
        # Translators: the title of the go to page dialog
        with GoToPageDialog(parent=self, title=_("Go To Page")) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                retval = dlg.GetValue()
                self.reader.go_to_page(retval)

    @only_when_reader_ready
    def onViewRenderedAsImage(self, event):
        # Translators: the title of the render page dialog
        with ViewPageAsImageDialog(self, _("Rendered Page"), style=wx.CLOSE_BOX) as dlg:
            dlg.Maximize()
            dlg.ShowModal()

    def onPreferences(self, event):
        dlg = PreferencesDialog(
            self,
            # Translators: the title of the application preferences dialog
            title=_("{app_name} Preferences").format(app_name=app.display_name),
        )
        with dlg:
            dlg.ShowModal()

    @only_when_reader_ready
    def onFind(self, event):
        # Translators: the title of the search dialog
        dlg = SearchBookDialog(parent=self, title=_("Search book"))
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
            self, title=_("Searching For '{term}'").format(term=term)
        )
        dlg.Show()
        self._add_search_results(request, dlg)

    @call_threaded
    def _add_search_results(self, request, dlg):
        search_func = self.reader.document.search
        doc_path = self.reader.document.filename
        total = 0
        for page, snip, section, pos in search_func(doc_path, request):
            if pos is None:
                wx.CallAfter(
                    dlg.progressbar.SetValue, round((page / request.to_page) * 100)
                )
                continue
            if not dlg.IsShown():
                break
            wx.CallAfter(dlg.addResult, page, snip, section, pos)
            self._latest_search_results.append((page, snip, section, pos))
            total += 1
        if dlg.IsShown():
            # Translators: the final title of the search results dialog
            # shown after the search is finished
            msg = _("Results | {total}").format(total=total)
            dlg.SetTitle(msg)
            speech.announce(msg, True)

    @only_when_reader_ready
    def onFindNext(self, event):
        result_count = len(self._latest_search_results)
        next_result = self._last_search_index + 1
        if not result_count or (next_result >= result_count):
            return wx.Bell()
        self._last_search_index = next_result
        page_number, *_, pos = self._latest_search_results[self._last_search_index]
        self.highlight_search_result(page_number, pos)

    @only_when_reader_ready
    def onFindPrev(self, event):
        result_count = len(self._latest_search_results)
        prev_result = self._last_search_index - 1
        if not result_count or (prev_result < 0):
            return wx.Bell()
        self._last_search_index = prev_result
        page_number, *_, pos = self._latest_search_results[self._last_search_index]
        self.highlight_search_result(page_number, pos)

    def onAbout(self, event):
        # Translators: the content of the about message
        about_msg = _(
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
        wx.MessageBox(
            about_msg,
            # Translators: the title of the about dialog
            _("About {app_name}").format(app_name=app.display_name),
            parent=self,
            style=wx.ICON_INFORMATION,
        )

    def open_file(self, filename):
        if not os.path.isfile(filename):
            self.populate_recent_file_list()
            return wx.MessageBox(
                # Translators: the content of an error message
                _("The file\n{file}\nwas not found.").format(file=filename),
                # Translators: the title of an error message
                _("File Not Found"),
                style=wx.ICON_ERROR,
            )
        if not self.reader.load(filename):
            return
        if self.reader.document.is_encrypted():
            self.decrypt_opened_document()
        self.renderItem.Enable(self.reader.document.supports_rendering)
        self.tocTreeCtrl.Expand(self.tocTreeCtrl.GetRootItem())
        wx.CallAfter(self.tocTreeCtrl.SetFocus)
        recent_files = config.conf["history"]["recently_opened"]
        if filename in recent_files:
            recent_files.remove(filename)
        recent_files.insert(0, filename)
        newfiles = recent_files if len(recent_files) < 10 else recent_files[:10]
        config.conf["history"]["recently_opened"] = newfiles
        config.save()
        self.populate_recent_file_list()

    def onRestartWithDebugMode(self, event):
        restart_application(debug=True)

    @property
    def content_text_ctrl_context_menu(self):
        menu = wx.Menu()
        entries = [
            (10, _("&Go To Page...\tCtrl-G"), _("Jump to a page"), BookRelatedMenuIds.goToPage),
            (20, _("&Find in Book...\tCtrl-F"), _("Search this book."), wx.ID_FIND),
            (21, "", "", None),
            (30, _("&Render Page...\tCtrl-R"), _("View a fully rendered version of this page."), BookRelatedMenuIds.viewRenderedAsImage),
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
        event.Skip(False)
        if self.reader.ready:
            pos = self.contentTextCtrl.PositionToCoords(
                self.contentTextCtrl.InsertionPoint
            )
            self.PopupMenu(self.content_text_ctrl_context_menu, pos=pos)

    def onOpenDocumentation(self, event):
        help_filename = f"bookworm.{'html' if app.is_frozen else 'md'}"
        lang = app.current_language.given_lang
        docs = paths.docs_path(lang, help_filename)
        wx.LaunchDefaultApplication(str(docs))

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
                self.Bind(wx.EVT_MENU, self.onRecentFileItem, item)
                self._recent_files_data.append((item, item.GetId(), filename))
                if self.reader.ready:
                    for (it, id, fn) in self._recent_files_data:
                        if fn == self.reader.document.filename:
                            it.Enable(False)

    def _reset_search_history(self):
        self._latest_search_results = []
        self._last_search_index = 0
        self._recent_search_term = ""

    @gui_thread_safe
    def highlight_search_result(self, page_number, pos):
        self.reader.go_to_page(page_number)
        self.contentTextCtrl.SetSelection(pos, pos + len(self._recent_search_term))

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

    def decrypt_opened_document(self):
        pwd = wx.GetPasswordFromUser(
            # Translators: the content of a dialog asking the user
            # for the password to decrypt the current e-book
            _(
                "This document is encrypted, and you need a password to access its content.\nPlease enter the password billow and press enter."
            ),
            # Translators: the title of a dialog asking the user to enter a password to decrypt the e-book
            "Enter Password",
            parent=self,
        )
        res = self.reader.document.decrypt(pwd.GetValue())
        if not res:
            wx.MessageBox(
                # Translators: the content of a message
                _("The password you've entered is invalid.\nPlease try again."),
                # Translators: the title of an error message
                _("Invalid Password"),
                parent=self,
                style=wx.ICON_ERROR,
            )
            return self.decrypt_opened_document()

