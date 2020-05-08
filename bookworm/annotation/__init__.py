# coding: utf-8

import wx
from bookworm import config
from bookworm.signals import reader_page_changed
from bookworm.resources import sounds
from bookworm.base_service import BookwormService
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from .annotation_gui import (
    AnnotationMenu,
    AnnotationsMenuIds,
    ANNOTATIONS_KEYBOARD_SHORTCUTS,
)
from .annotator import Bookmarker, NoteTaker, Book, Note, Bookmark


log = logger.getChild(__name__)


class AnnotationService(BookwormService):
    name = "annotation"
    stateful_menu_ids = AnnotationsMenuIds
    has_gui = True

    def __post_init__(self):
        if config.conf["general"]["play_page_note_sound"]:
            reader_page_changed.connect(self.play_sound_if_note, sender=self.reader)
        if config.conf["general"]["highlight_bookmarked_positions"]:
            reader_page_changed.connect(
                self.highlight_bookmarked_positions, sender=self.reader
            )

    def process_menubar(self, menubar):
        self.menu = AnnotationMenu(self, menubar)

    def get_contextmenu_items(self):
        rv = [
            (3, _("&Bookmark...\tCtrl-B"), _("Bookmark the current location"), AnnotationsMenuIds.addBookmark),
            (4, _("Co&mment...\tCtrl-m"), _("Add a comment at the current location"), AnnotationsMenuIds.addNote),
            (5, "", "", None),
        ]
        if self.view.contentTextCtrl.GetStringSelection():
            rv.insert(0, (0, _("Highlight Selection\tCtrl-Shift-H"), _("Highlight and save selected text."), AnnotationsMenuIds.quoteSelection),)
        return rv

    def get_toolbar_items(self):
        return [
            # Translators: the label of a button in the application toolbar
            (32, "bookmark", _("Bookmark"), AnnotationsMenuIds.addBookmark),
            # Translators: the label of a button in the application toolbar
            (33, "comment", _("Comment"), AnnotationsMenuIds.addNote),
            (34, "", "", None),
        ]

    def get_keyboard_shourtcuts(self):
        return ANNOTATIONS_KEYBOARD_SHORTCUTS

    @classmethod
    def _annotations_page_handler(cls, reader):
        q_count = (
            Note.query.filter(Book.identifier == reader.document.identifier)
            .filter_by(page_number=reader.current_page)
            .count()
        )
        if q_count:
            sounds.has_note.play()

    @classmethod
    def play_sound_if_note(cls, sender, current, prev):
        """Play a sound if the current page has a note."""
        wx.CallLater(150, cls._annotations_page_handler, sender)

    @classmethod
    def highlight_bookmarked_positions(cls, sender, current, prev):
        bookmarks = (
            Bookmark.query.filter(Book.identifier == sender.document.identifier)
            .filter(Bookmark.page_number == sender.current_page)
            .all()
        )
        if not bookmarks:
            return
        for bookmark in bookmarks:
            cls.highlight_containing_line(bookmark.position, sender.view)

    @classmethod
    def highlight_containing_line(cls, pos, view, fg="white", bg="black"):
        fg, bg = [wx.Colour(fg), wx.Colour(bg)]
        lft, rgt = view.get_containing_line(pos)
        wx.CallAfter(
            view.contentTextCtrl.SetStyle, lft, rgt, wx.TextAttr(fg, bg)
        )


