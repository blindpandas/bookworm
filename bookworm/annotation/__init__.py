# coding: utf-8

import wx
from bookworm import config
from bookworm.signals import reader_page_changed, reader_book_loaded, reader_book_unloaded
from bookworm.resources import sounds
from bookworm.base_service import BookwormService
from bookworm.utils import gui_thread_safe
from bookworm.concurrency import call_threaded
from bookworm.logger import logger
from .annotation_gui import (
    AnnotationSettingsPanel,
    AnnotationMenu,
    AnnotationsMenuIds,
    ANNOTATIONS_KEYBOARD_SHORTCUTS,
)
from .annotator import Bookmarker, NoteTaker, Quoter


log = logger.getChild(__name__)


ANNOTATION_CONFIG_SPEC = {
    "annotation": dict(
        use_visuals="boolean(default=True)",
        play_sound_for_comments="boolean(default=True)",
        exclude_named_bookmarks_when_jumping="boolean(default=False)",
    )
}


class AnnotationService(BookwormService):
    name = "annotation"
    config_spec = ANNOTATION_CONFIG_SPEC
    stateful_menu_ids = AnnotationsMenuIds
    has_gui = True

    def __post_init__(self):
        self.view.contentTextCtrl.Bind(wx.EVT_KEY_UP, self.onKeyUp, self.view.contentTextCtrl)
        reader_book_loaded.connect(self.on_book_load, sender=self.reader)
        reader_book_unloaded.connect(self.on_book_unload, sender=self.reader)
        reader_page_changed.connect(self.comments_page_handler, sender=self.reader)
        reader_page_changed.connect(
            self.highlight_bookmarked_positions, sender=self.reader
        )
        reader_page_changed.connect(self.highlight_highlighted_text, sender=self.reader)

    def process_menubar(self, menubar):
        self.menu = AnnotationMenu(self, menubar)

    def get_contextmenu_items(self):
        rv = [
            (
                3,
                _("&Bookmark...\tCtrl-B"),
                _("Bookmark the current location"),
                AnnotationsMenuIds.addBookmark,
            ),
            (
                4,
                _("&Named Bookmark...\tCtrl-Shift-B"),
                _("Bookmark the current location"),
                AnnotationsMenuIds.addNamedBookmark,
            ),
            (
                5,
                _("Co&mment...\tCtrl-m"),
                _("Add a comment at the current location"),
                AnnotationsMenuIds.addNote,
            ),
            (6, "", "", None),
        ]
        if self.view.contentTextCtrl.GetStringSelection():
            rv.insert(
                0,
                (
                    0,
                    _("Highlight Selection\tCtrl-Shift-H"),
                    _("Highlight and save selected text."),
                    AnnotationsMenuIds.quoteSelection,
                ),
            )
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

    def get_settings_panels(self):
        return [
            # Translators: the label of a page in the settings dialog
            (30, "annotation", AnnotationSettingsPanel, _("Annotation"))
        ]

    def onKeyUp(self, event):
        event.Skip()
        if not self.reader.ready:
            return
        if event.GetKeyCode() == wx.WXK_F2:
            if event.GetModifiers() == wx.MOD_SHIFT:
                self.go_to_bookmark(foreword=False)
            else:
                self.go_to_bookmark(foreword=True)

    def go_to_bookmark(self, *, foreword):
        page_number = self.reader.current_page
        start, end = self.view.get_containing_line(self.view.get_insertion_point())
        if foreword:
            bookmark = self.bookmarker.get_first_after(page_number, end)
        else:        
            bookmark = self.bookmarker.get_first_before(page_number, start)
        if bookmark is not None:
            self.reader.go_to_page(bookmark.page_number, bookmark.position)
            self.view.select_text(*self.view.get_containing_line(bookmark.position))
        else:
            sounds.navigation.play()

    def on_book_load(self, sender):
        self.bookmarker = Bookmarker(sender)

    def on_book_unload(self, sender):
        self.bookmarker = None

    @classmethod
    @call_threaded
    def comments_page_handler(cls, sender, current, prev):
        comments = NoteTaker(sender).get_for_page()
        if comments.count():
            if config.conf["annotation"]["play_sound_for_comments"]:
                wx.CallLater(150, lambda: sounds.has_note.play())
        for comment in comments:
            cls.style_comment(sender.view, comment.position)

    @classmethod
    @call_threaded
    def highlight_bookmarked_positions(cls, sender, current, prev):
        if not config.conf["annotation"]["use_visuals"]:
            return
        bookmarks = Bookmarker(sender).get_for_page()
        if not bookmarks.count():
            return
        for bookmark in bookmarks:
            cls.style_bookmark(sender.view, bookmark.position)

    @classmethod
    @call_threaded
    def highlight_highlighted_text(cls, sender, current, prev):
        if not config.conf["annotation"]["use_visuals"]:
            return
        quoter = Quoter(sender)
        for_page = quoter.get_for_page()
        if not for_page.count():
            return
        for quote in for_page:
            cls.style_highlight(sender.view, quote.start_pos, quote.end_pos)

    @staticmethod
    @gui_thread_safe
    def style_bookmark(view, position, enable=True):
        if not config.conf["annotation"]["use_visuals"]:
            return
        start, end = view.get_containing_line(position)
        if config.conf["annotation"]["use_visuals"]:
            attr = wx.TextAttr(view.contentTextCtrl.GetDefaultStyle())
            attr.SetFontUnderlined(enable)
            view.contentTextCtrl.SetStyle(start, end, attr)

    @staticmethod
    @gui_thread_safe
    def style_highlight(view, start, end, enable=True):
        if not config.conf["annotation"]["use_visuals"]:
            return
        if enable:
            view.highlight_range(start, end, background=wx.YELLOW)
        else:
            view.clear_highlight(start, end)

    @staticmethod
    @gui_thread_safe
    def style_comment(view, pos, enable=True):
        if not config.conf["annotation"]["use_visuals"]:
            return
