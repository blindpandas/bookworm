# coding: utf-8

import sys
import os
import wx
import threading
import enum
import webbrowser
from pathlib import Path
from slugify import slugify
from bookworm import config
from bookworm import paths
from bookworm import app
from bookworm.annotator import Bookmarker
from bookworm.concurrency import call_threaded
from bookworm import speech
from bookworm.speech.enumerations import SynthState
from bookworm.reader import EBookReader
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from .decorators import only_when_reader_ready
from ..preferences_dialog import PreferencesDialog
from .core_dialogs import (
    GoToPageDialog,
    SearchBookDialog,
    SearchResultsDialog,
    ViewPageAsImageDialog,
    VoiceProfileDialog,
)
from .annotation_dialogs import (
    NoteEditorDialog,
    ViewAnnotationsDialog,
    ExportNotesDialog,
    highlight_containing_line,
)


log = logger.getChild(__name__)


class BookRelatedMenuIds(enum.IntEnum):
    """Declares  menu ids for items which are enabled/disabled
    based on whether a book is loaded or not.
    """

    # File
    export = wx.ID_SAVEAS
    closeCurrentFile = 211
    # Tools
    goToPage = 221
    searchBook = wx.ID_FIND
    findNext = 222
    findPrev = 223
    viewRenderedAsImage = 224
    # Speech
    play = 251
    stop = 252
    pauseToggle = 253
    rewind = wx.ID_BACKWARD
    fastforward = wx.ID_FORWARD
    # Annotations
    addBookmark = 241
    addNote = 242
    viewBookmarks = 243
    viewNotes = 244
    ExportNotes = 245


class ViewerMenuIds(enum.IntEnum):
    """Declares menu ids for all other menu items."""

    # Tools menu
    preferences = wx.ID_PREFERENCES
    # Speech menu
    voiceProfiles = 257
    deactivateVoiceProfiles = wx.ID_REVERT
    # Help Menu
    documentation = 801
    website = 802
    license = 803
    about = 804


class MenubarProvider:
    """The application menubar."""

    def __init__(self):
        self.menuBar = wx.MenuBar()
        self._search_list_lock = threading.RLock()
        self._reset_search_history()

        # The menu
        fileMenu = wx.Menu()
        toolsMenu = wx.Menu()
        speechMenu = wx.Menu()
        annotationsMenu = wx.Menu()
        helpMenu = wx.Menu()
        # A submenu for recent files
        self.recentFilesMenu = wx.Menu()

        # add items to the menu
        # File menu
        fileMenu.Append(wx.ID_OPEN)
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_SAVEAS, "&Save As Plane Text...")
        fileMenu.AppendSeparator()
        fileMenu.Append(
            BookRelatedMenuIds.closeCurrentFile,
            "&Close Current Book\tCtrl-W",
            "Close current file",
        )
        fileMenu.AppendSeparator()
        fileMenu.AppendSubMenu(
            self.recentFilesMenu,
            "&Recent Books",
            "Opens a list of recently opened books.",
        )
        self.recentFilesMenu.Append(
            wx.ID_CLEAR, "Clear list", "Clear the recent books list."
        )
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT)
        # Tools menu
        toolsMenu.Append(
            BookRelatedMenuIds.goToPage, "&Go To Page...\tCtrl-g", "Go to page"
        )
        toolsMenu.Append(wx.ID_FIND, "&Find in Book...\tCtrl-F", "Search this book.")
        toolsMenu.Append(
            BookRelatedMenuIds.findNext, "&Find &Next...\tF3", "Find next occurrence."
        )
        toolsMenu.Append(
            BookRelatedMenuIds.findPrev,
            "&Find &Previous...\tShift-F3",
            "Find previous occurrence.",
        )
        self.renderItem = toolsMenu.Append(
            BookRelatedMenuIds.viewRenderedAsImage,
            "&Render Page\tCtrl-R",
            "View a fully rendered version of this page.",
        )
        # Speech menu
        speechMenu.Append(BookRelatedMenuIds.play, "&Play\tF5", "Start reading aloud")
        speechMenu.Append(
            BookRelatedMenuIds.pauseToggle,
            "Pa&use/Resume\tF6",
            "Pause/Resume reading aloud",
        )
        speechMenu.Append(BookRelatedMenuIds.stop, "&Stop\tF7", "Stop reading aloud")
        speechMenu.Append(
            BookRelatedMenuIds.rewind,
            "&Rewind\tAlt-LeftArrow",
            "Skip to previous paragraph",
        )
        speechMenu.Append(
            BookRelatedMenuIds.fastforward,
            "&Fast Forward\tAlt-RightArrow",
            "Skip to next paragraph",
        )
        speechMenu.Append(
            ViewerMenuIds.voiceProfiles,
            "&Voice Profiles\tCtrl-Shift-V",
            "Manage voice profiles.",
        )
        speechMenu.Append(
            ViewerMenuIds.deactivateVoiceProfiles,
            "&Deactivate Active Voice Profile",
            "Deactivate the active voice profile.",
        )
        toolsMenu.Append(
            wx.ID_PREFERENCES, "&Preferences...\tCtrl-Shift-P", "Configure application"
        )
        # Annotations menu
        annotationsMenu.Append(
            BookRelatedMenuIds.addBookmark,
            "Add &Bookmark...\tCtrl-B",
            "Bookmark the current location",
        )
        annotationsMenu.Append(
            BookRelatedMenuIds.addNote,
            "Add &Note...\tCtrl-n",
            "Add a note at the current location",
        )
        annotationsMenu.Append(
            BookRelatedMenuIds.viewBookmarks,
            "&View Bookmarks...\tCtrl-Shift-B",
            "View added bookmarks",
        )
        annotationsMenu.Append(
            BookRelatedMenuIds.viewNotes,
            "&Manage Notes...\tCtrl-Shift-N",
            "View, edit, and remove notes.",
        )
        annotationsMenu.Append(
            BookRelatedMenuIds.ExportNotes,
            "Notes &Exporter...",
            "Export notes to a file.",
        )
        # Help menu
        helpMenu.Append(
            ViewerMenuIds.documentation, "&User guide...\tF1", "View Bookworm manuals "
        )
        helpMenu.Append(
            ViewerMenuIds.website, "&Bookworm website...", "Visit the official website."
        )
        helpMenu.Append(
            ViewerMenuIds.license,
            "&License",
            "View legal information about this program .",
        )
        helpMenu.Append(
            ViewerMenuIds.about,
            "&About Bookworm...",
            "General information about this program.",
        )

        # Bind the menu event to an event handler
        # File menu event handlers
        self.Bind(wx.EVT_MENU, self.onOpenEBook, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.onExportAsPlaneText, id=wx.ID_SAVEAS)
        self.Bind(
            wx.EVT_MENU, self.onCloseCurrentFile, id=BookRelatedMenuIds.closeCurrentFile
        )
        self.Bind(wx.EVT_MENU, self.onClearRecentFileList, id=wx.ID_CLEAR)
        self.Bind(wx.EVT_MENU, self.onClose, id=wx.ID_EXIT)

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

        # Speech menu event handlers
        self.Bind(wx.EVT_MENU, self.onPlay, id=BookRelatedMenuIds.play)
        self.Bind(wx.EVT_MENU, self.onPauseToggle, id=BookRelatedMenuIds.pauseToggle)
        self.Bind(
            wx.EVT_MENU, lambda e: self.reader.rewind(), id=BookRelatedMenuIds.rewind
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.reader.fastforward(),
            id=BookRelatedMenuIds.fastforward,
        )
        self.Bind(wx.EVT_MENU, self.onStop, id=BookRelatedMenuIds.stop)
        self.Bind(wx.EVT_MENU, self.onVoiceProfiles, id=ViewerMenuIds.voiceProfiles)
        self.Bind(
            wx.EVT_MENU,
            self.onDeactivateVoiceProfile,
            id=ViewerMenuIds.deactivateVoiceProfiles,
        )

        # Annotations menu event handlers
        self.Bind(wx.EVT_MENU, self.onAddBookmark, id=BookRelatedMenuIds.addBookmark)
        self.Bind(wx.EVT_MENU, self.onAddNote, id=BookRelatedMenuIds.addNote)
        self.Bind(
            wx.EVT_MENU, self.onViewBookmarks, id=BookRelatedMenuIds.viewBookmarks
        )
        self.Bind(wx.EVT_MENU, self.onViewNotes, id=BookRelatedMenuIds.viewNotes)
        self.Bind(wx.EVT_MENU, self.onNotesExporter, id=BookRelatedMenuIds.ExportNotes)

        # Help menu event handlers
        help_filename = f"bookworm.{'md' if app.debug else 'html'}"
        docs = paths.docs_path(help_filename)
        self.Bind(
            wx.EVT_MENU,
            lambda e: wx.LaunchDefaultApplication(str(docs)),
            id=ViewerMenuIds.documentation,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: webbrowser.open(app.website),
            id=ViewerMenuIds.website,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: wx.LaunchDefaultApplication(str(DOCS_PATH / "license.txt")),
            id=ViewerMenuIds.license,
        )
        self.Bind(wx.EVT_MENU, self.onAbout, id=ViewerMenuIds.about)

        # and put the menu on the menubar
        self.menuBar.Append(fileMenu, "&File")
        self.menuBar.Append(toolsMenu, "&Tools")
        self.menuBar.Append(speechMenu, "&Speech")
        self.menuBar.Append(annotationsMenu, "&Annotations")
        self.menuBar.Append(helpMenu, "&Help")
        self.SetMenuBar(self.menuBar)
        # Disable this when no voice profile is active
        self.menuBar.FindItemById(wx.ID_REVERT).Enable(False)

        # Populate the recent files submenu
        self._recent_files_data = []
        self.populate_recent_file_list()

    def onOpenEBook(self, event):
        last_folder = config.conf["history"]["last_folder"]
        if not os.path.isdir(last_folder):
            last_folder = str(Path.home())
        openFileDlg = wx.FileDialog(
            self,
            message="Choose an e-book",
            defaultDir=last_folder,
            wildcard=self._get_ebooks_wildcards(),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if openFileDlg.ShowModal() == wx.ID_OK:
            filename = openFileDlg.GetPath().strip()
            if filename:
                self.open_file(filename)
                config.conf["history"]["last_folder"] = os.path.split(filename)[0]
                config.save()
        openFileDlg.Destroy()

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
        self.Close()

    @only_when_reader_ready
    def onCloseCurrentFile(self, event):
        self.unloadCurrentEbook()
        self.populate_recent_file_list()

    @only_when_reader_ready
    def onGoToPage(self, event):
        dlg = GoToPageDialog(parent=self, title="Go To Page")
        if dlg.ShowModal() == wx.ID_OK:
            retval = dlg.GetValue()
            dlg.Destroy()
            if not retval:
                return
            self.reader.go_to_page(retval)
            self._last_go_to_page = retval

    @only_when_reader_ready
    def onViewRenderedAsImage(self, event):
        with ViewPageAsImageDialog(self, "Rendered Page", style=wx.CLOSE_BOX) as dlg:
            dlg.Maximize()
            dlg.ShowModal()

    def onVoiceProfiles(self, event):
        with VoiceProfileDialog(self, title="Voice Profiles") as dlg:
            dlg.ShowModal()

    def onDeactivateVoiceProfile(self, event):
        config.conf.active_profile = None
        self.reader.tts.configure_engine()
        self.menuBar.FindItemById(wx.ID_REVERT).Enable(False)

    @only_when_reader_ready
    def onAddBookmark(self, event):
        dlg = wx.TextEntryDialog(self, "Bookmark title:", "Bookmark This Location")
        insertionPoint = self.contentTextCtrl.GetInsertionPoint()
        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.GetValue().strip()
            if not value:
                return wx.Bell()
            Bookmarker(self.reader).create(title=value, position=insertionPoint)
            if config.conf["general"]["highlight_bookmarked_positions"]:
                highlight_containing_line(insertionPoint, self)
        dlg.Destroy()

    @only_when_reader_ready
    def onAddNote(self, event):
        insertionPoint = self.contentTextCtrl.GetInsertionPoint()
        dlg = NoteEditorDialog(self, self.reader, pos=insertionPoint)
        dlg.Show()

    def onViewBookmarks(self, event):
        dlg = ViewAnnotationsDialog(
            self,
            type_="bookmark",
            title=f"Bookmarks | {self.reader.current_book.title}",
        )
        with dlg:
            dlg.ShowModal()

    def onViewNotes(self, event):
        dlg = ViewAnnotationsDialog(
            self, type_="note", title=f"Notes | {self.reader.current_book.title}"
        )
        with dlg:
            dlg.ShowModal()

    def onNotesExporter(self, event):
        dlg = ExportNotesDialog(
            self.reader, self, title=f"Export Notes | {self.reader.current_book.title}"
        )
        dlg.Show()

    def onPreferences(self, event):
        with PreferencesDialog(self, title=f"{app.display_name} Preferences") as dlg:
            dlg.ShowModal()

    @only_when_reader_ready
    @call_threaded
    def onExportAsPlaneText(self, event):
        book_title = slugify(self.reader.current_book.title)
        filename, _ = wx.FileSelectorEx(
            "Save As",
            default_path=wx.GetUserHome(),
            default_filename=f"{book_title}.txt",
            wildcard="Plane Text (*.txt)|.txt",
            flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            parent=self,
        )
        if not filename.strip():
            return
        total = len(self.reader.document)
        dlg = wx.ProgressDialog(
            "Exporting Book",
            "Converting your book to plane text.",
            parent=self,
            maximum=total - 1,
            style=wx.PD_APP_MODAL | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE,
        )
        export_func = self.reader.document.export_to_text
        for progress in export_func(self.reader.document.filename, filename):
            dlg.Update(progress, "Converting book...")
        dlg.Close()
        dlg.Destroy()

    @only_when_reader_ready
    def onFind(self, event):
        dlg = SearchBookDialog(parent=self, title="Search book")
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
        dlg = SearchResultsDialog(self, title=f"Searching For '{term}'")
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
            with self._search_list_lock:
                self._latest_search_results.append((page, snip, section, pos))
            total += 1
        if dlg.IsShown():
            dlg.SetTitle(f"Found {total} results.")
            speech.announce(f"Found {total} results.", True)

    @only_when_reader_ready
    def onFindNext(self, event):
        result_count = len(self._latest_search_results)
        next_result = self._last_search_index + 1
        if not result_count or (next_result >= result_count):
            return wx.Bell()
        self._last_search_index = next_result
        with self._search_list_lock:
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
        wx.MessageBox(
            app.about_msg,
            f"About {app.display_name}",
            parent=self,
            style=wx.ICON_INFORMATION,
        )

    def onPlay(self, event):
        if not self.reader.tts.is_ready:
            self.reader.tts.initialize()
        elif self.reader.tts.engine.state is SynthState.busy:
            return wx.Bell()
        self.reader.speak_current_page()

    def onPauseToggle(self, event):
        if self.reader.tts.is_ready:
            if self.reader.tts.engine.state is SynthState.busy:
                self.reader.tts.engine.pause()
                return speech.announce("Paused")
            elif self.reader.tts.engine.state is SynthState.paused:
                self.reader.tts.engine.resume()
                return speech.announce("Resumed")
        wx.Bell()

    def onStop(self, event):
        if (
            self.reader.tts.is_ready
            and self.reader.tts.engine.state is not SynthState.ready
        ):
            self.reader.tts.engine.stop()
            return speech.announce("Stopped")
        wx.Bell()

    def open_file(self, filename):
        if not os.path.isfile(filename):
            self.populate_recent_file_list()
            return wx.MessageBox(
                f"The file\n{filename}\nwas not found.",
                "Missing File",
                style=wx.ICON_ERROR,
            )
        self.reader.load(filename)
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

    def populate_recent_file_list(self):
        for item, _, filename in self._recent_files_data:
            self.recentFilesMenu.Delete(item)
        self._recent_files_data.clear()
        recent_files = config.conf["history"]["recently_opened"]
        if len(recent_files) == 0:
            _no_files = self.recentFilesMenu.Append(
                -1, "(No recent books)", "No recent books"
            )
            _no_files.Enable(False)
            self._recent_files_data.append((_no_files, -1, ""))
        else:
            recent_files = (file for file in recent_files if os.path.exists(file))
            for idx, filename in enumerate(recent_files):
                fname = os.path.split(filename)[-1]
                item = self.recentFilesMenu.Append(
                    wx.ID_ANY, f"{idx + 1}. {fname}", "Open this book"
                )
                self.Bind(wx.EVT_MENU, self.onRecentFileItem, item)
                self._recent_files_data.append((item, item.GetId(), filename))
                if self.reader.ready:
                    for (it, id, fn) in self._recent_files_data:
                        if fn == self.reader.document.filename:
                            it.Enable(False)
        self.recentFilesMenu.FindItemById(wx.ID_CLEAR).Enable(
            self._recent_files_data[0][2] != ""
        )

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
                rv.append(f"{cls.name} ({ext})|{ext}|")
                all_exts.append(ext)
        rv[-1] = rv[-1].rstrip("|")
        allfiles = ";".join(all_exts)
        allfiles_display = " ".join(e for e in all_exts)
        rv.insert(0, f"Supported E-Book Formats ({allfiles_display})|{allfiles}|")
        return "".join(rv)

    def decrypt_opened_document(self):
        pwd = wx.GetPasswordFromUser(
            "This document is encrypted, and you need a password to access its content.\nPlease enter the password billow and press enter.",
            "Enter Password",
            parent=self,
        )
        res = self.reader.document.decrypt(pwd.GetValue())
        if not res:
            wx.MessageBox(
                "The password you've entered is invalid.\nPlease try again.",
                "Invalid Password",
                parent=self,
                style=wx.ICON_ERROR,
            )
            return self.decrypt_opened_document()
