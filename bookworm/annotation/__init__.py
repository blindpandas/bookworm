# coding: utf-8

import wx

from bookworm import config, speech
from bookworm.logger import logger
from bookworm.resources import sounds
from bookworm.service import BookwormService
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    reading_position_change,
)
from bookworm.utils import gui_thread_safe

from .annotation_gui import (
    ANNOTATIONS_KEYBOARD_SHORTCUTS,
    AnnotationMenu,
    AnnotationSettingsPanel,
    AnnotationsMenuIds,
)
from .annotation_models import Note, Quote
from .annotator import Bookmarker, NoteTaker, Quoter

log = logger.getChild(__name__)


ANNOTATION_CONFIG_SPEC = {
    "annotation": dict(
        use_visuals="boolean(default=True)",
        play_sound_for_comments="boolean(default=True)",
        select_bookmarked_line_on_jumping="boolean(default=True)",
        speak_bookmarks_on_jumping="boolean(default=True)",
    )
}


class AnnotationService(BookwormService):
    name = "annotation"
    config_spec = ANNOTATION_CONFIG_SPEC
    stateful_menu_ids = AnnotationsMenuIds
    has_gui = True

    def __post_init__(self):
        self.__state = {}
        self.view.contentTextCtrl.Bind(
            wx.EVT_KEY_UP, self.onKeyUp, self.view.contentTextCtrl
        )
        self.view.add_load_handler(
            lambda red: wx.CallAfter(self._check_is_virtual, red)
        )
        reader_book_unloaded.connect(self.on_book_unload, sender=self.reader)
        reader_page_changed.connect(self.comments_page_handler, sender=self.reader)
        reader_page_changed.connect(
            self.highlight_bookmarked_positions, sender=self.reader
        )
        reader_page_changed.connect(self.highlight_highlighted_text, sender=self.reader)

    def process_menubar(self, menubar):
        self.menu = AnnotationMenu(self)
        # Translators: the label of an item in the application menubar
        return (30, self.menu, _("&Annotation"))

    def get_contextmenu_items(self):
        if self.reader.document.uri.view_args.get("is_virtual", False):
            return []
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

    def get_keyboard_shortcuts(self):
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
        forward = event.GetModifiers() != wx.MOD_SHIFT
        if event.GetKeyCode() == wx.WXK_F2:
            bookmark = self.get_annotation(Bookmarker, foreword=forward)
            if bookmark is None:
                no_annotation_msg = (
                    # Translators: spoken message
                    _("No next bookmark")
                    if forward
                    # Translators: spoken message
                    else _("No previous bookmark")
                )
                speech.announce(no_annotation_msg)
                sounds.invalid.play()
                return
            self.reader.go_to_page(bookmark.page_number, bookmark.position)
            if config.conf["annotation"]["select_bookmarked_line_on_jumping"]:
                self.view.select_text(*self.view.get_containing_line(bookmark.position))
            # Translators: spoken message when jumping to a bookmark
            msg = _("Bookmark")
            if bookmark.title:
                msg += f": {bookmark.title}"
            text_to_announce = (
                msg if config.conf["annotation"]["speak_bookmarks_on_jumping"] else None
            )
            reading_position_change.send(
                self.view,
                position=bookmark.position,
                text_to_announce=text_to_announce,
                tts_speech_prefix=msg,
            )
            sounds.navigation.play()
        elif event.KeyCode == wx.WXK_F8:
            comment = self.get_annotation(NoteTaker, foreword=forward)
            if not isinstance(comment, Note):
                no_annotation_msg = (
                    # Translators: spoken message
                    _("No next comment")
                    if forward
                    # Translators: spoken message
                    else _("No previous comment")
                )
                speech.announce(no_annotation_msg)
                sounds.invalid.play()
                return
            self.reader.go_to_page(comment.page_number, comment.position)
            self.view.select_text(*self.view.get_containing_line(comment.position))
            reading_position_change.send(
                self.view,
                position=comment.position,
                # Translators: spoken message when jumping to a comment
                text_to_announce=_("Comment: {comment}").format(
                    comment=comment.content
                ),
            )
            sounds.navigation.play()
        elif event.KeyCode == wx.WXK_F9:
            sel_range = self.view.get_selection_range()
            if sel_range.start != sel_range.stop:
                self.view.unselect_text()
            highlight = self.get_annotation(Quoter, foreword=forward)
            if not isinstance(highlight, Quote):
                no_annotation_msg = (
                    # Translators: spoken message
                    _("No next highlight")
                    if forward
                    # Translators: spoken message
                    else _("No previous highlight")
                )
                speech.announce(no_annotation_msg)
                sounds.invalid.play()
                return
            self.reader.go_to_page(highlight.page_number, highlight.start_pos)
            self.view.select_text(highlight.start_pos, highlight.end_pos)
            reading_position_change.send(
                self.view,
                position=highlight.start_pos,
                text_to_announce=_("Highlight"),
            )
            sounds.navigation.play()

    def get_annotation(self, annotator_cls, *, foreword):
        if not (annotator := self.__state.get(annotator_cls.__name__)):
            annotator = self.__state.setdefault(
                annotator_cls.__name__, annotator_cls(self.reader)
            )
        page_number = self.reader.current_page
        start, end = self.view.get_containing_line(self.view.get_insertion_point())
        if foreword:
            annot = annotator.get_first_after(page_number, end)
        else:
            annot = annotator.get_first_before(page_number, start)
        return annot

    def _check_is_virtual(self, sender):
        enable = not sender.document.uri.view_args.get("is_virtual", False)
        self.view.synchronise_menu(self.stateful_menu_ids, enable)

    def on_book_unload(self, sender):
        self.__state.clear()

    @classmethod
    def comments_page_handler(cls, sender, current, prev):
        comments = NoteTaker(sender).get_for_page()
        if comments.count():
            if config.conf["annotation"]["play_sound_for_comments"]:
                wx.CallLater(150, lambda: sounds.has_note.play())
        for comment in comments:
            cls.style_comment(sender.view, comment.position)

    @classmethod
    def highlight_bookmarked_positions(cls, sender, current, prev):
        if not config.conf["annotation"]["use_visuals"]:
            return
        bookmarks = Bookmarker(sender).get_for_page()
        if not bookmarks.count():
            return
        for bookmark in bookmarks:
            cls.style_bookmark(sender.view, bookmark.position)

    @classmethod
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
            attr = wx.TextAttr()
            view.contentTextCtrl.GetStyle(start, attr)
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
