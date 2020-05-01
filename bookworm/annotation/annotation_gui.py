# coding: utf-8

import wx
from enum import IntEnum
from bookworm import config
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from .annotator import Bookmarker
from .annotation_dialogs import (
    NoteEditorDialog,
    ViewAnnotationsDialog,
    ExportNotesDialog,
)


log = logger.getChild(__name__)


class AnnotationsMenuIds(IntEnum):
    addBookmark = 241
    addNote = 242
    viewBookmarks = 243
    viewNotes = 244
    ExportNotes = 245


ANNOTATIONS_KEYBOARD_SHORTCUTS = {
    AnnotationsMenuIds.addBookmark: "Ctrl-B",
    AnnotationsMenuIds.addNote: "Ctrl-N",
    AnnotationsMenuIds.viewBookmarks: "Ctrl-Shift-B",
    AnnotationsMenuIds.viewNotes: "Ctrl-Shift-N",
}


class AnnotationMenu(wx.Menu):
    """Annotation menu."""

    def __init__(self, service, menubar):
        super().__init__()
        self.service = service
        self.view = service.view
        self.reader = service.reader
        self.menubar = menubar

        # Add menu items
        self.Append(
            AnnotationsMenuIds.addBookmark,
            # Translators: the label of an item in the application menubar
            _("Add &Bookmark...\tCtrl-B"),
            # Translators: the help text of an item in the application menubar
            _("Bookmark the current location"),
        )
        self.Append(
            AnnotationsMenuIds.addNote,
            # Translators: the label of an item in the application menubar
            _("Take &Note...\tCtrl-N"),
            # Translators: the help text of an item in the application menubar
            _("Add a note at the current location"),
        )
        self.Append(
            AnnotationsMenuIds.viewBookmarks,
            # Translators: the label of an item in the application menubar
            _("&View Bookmarks...\tCtrl-Shift-B"),
            # Translators: the help text of an item in the application menubar
            _("View added bookmarks"),
        )
        self.Append(
            AnnotationsMenuIds.viewNotes,
            # Translators: the label of an item in the application menubar
            _("&Manage Notes...\tCtrl-Shift-N"),
            # Translators: the help text of an item in the application menubar
            _("View, edit, and remove notes."),
        )
        self.Append(
            AnnotationsMenuIds.ExportNotes,
            # Translators: the label of an item in the application menubar
            _("Notes &Exporter") + "...",
            # Translators: the help text of an item in the application menubar
            _("Export notes to a file."),
        )

        # Translators: the label of an item in the application menubar
        self.menubar.Insert(2, self, _("&Annotations"))

        # EventHandlers
        self.view.Bind(wx.EVT_MENU, self.onAddBookmark, id=AnnotationsMenuIds.addBookmark)
        self.view.Bind(wx.EVT_MENU, self.onAddNote, id=AnnotationsMenuIds.addNote)
        self.view.Bind(
            wx.EVT_MENU, self.onViewBookmarks, id=AnnotationsMenuIds.viewBookmarks
        )
        self.view.Bind(wx.EVT_MENU, self.onViewNotes, id=AnnotationsMenuIds.viewNotes)
        self.view.Bind(wx.EVT_MENU, self.onNotesExporter, id=AnnotationsMenuIds.ExportNotes)

    def onAddBookmark(self, event):
        dlg = wx.TextEntryDialog(
            self.view,
            # Translators: the label of an edit field to enter the title for a new bookmark
            _("Bookmark title:"),
            # Translators: the title of a dialog to create a new bookmark
            _("Bookmark This Location"),
        )
        insertionPoint = self.view.contentTextCtrl.GetInsertionPoint()
        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.GetValue().strip()
            if not value:
                return wx.Bell()
            Bookmarker(self.reader).create(title=value, position=insertionPoint)
            if config.conf["general"]["highlight_bookmarked_positions"]:
                self.service.highlight_containing_line(insertionPoint, self.view)
        dlg.Destroy()

    def onAddNote(self, event):
        insertionPoint = self.view.contentTextCtrl.GetInsertionPoint()
        with NoteEditorDialog(self.view, self.reader, pos=insertionPoint) as dlg:
            dlg.ShowModal()

    def onViewBookmarks(self, event):
        dlg = ViewAnnotationsDialog(
            self.view,
            type_="bookmark",
            # Translators: the title of a dialog to view bookmarks
            title=_("Bookmarks | {book}").format(book=self.reader.current_book.title),
        )
        with dlg:
            dlg.ShowModal()

    def onViewNotes(self, event):
        dlg = ViewAnnotationsDialog(
            self.view,
            type_="note",
            # Translators: the title of a dialog to view notes
            title=_("Notes | {book}").format(book=self.reader.current_book.title),
        )
        with dlg:
            dlg.ShowModal()

    def onNotesExporter(self, event):
        dlg = ExportNotesDialog(
            self.reader,
            self.view,
            # Translators: the title of a dialog for exporting notes
            title=_("Export Notes | {book}").format(
                book=self.reader.current_book.title
            ),
        )
        dlg.Show()

