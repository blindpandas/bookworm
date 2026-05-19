
import wx

from bookworm import config, speech
from bookworm.database.models import Note, Quote
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
from .annotator import Bookmarker, NoteTaker, Quoter

log = logger.getChild(__name__)


ANNOTATION_CONFIG_SPEC = {
    "annotation": dict(
        use_visuals="boolean(default=True)",
        select_bookmarked_line_on_jumping="boolean(default=True)",
        speak_bookmarks_on_jumping="boolean(default=True)",
        audable_indication_of_annotations_when_navigating_text="boolean(default=True)",
        spoken_indication_of_annotations_when_navigating_text="boolean(default=True)",
    )
}


class AnnotationService(BookwormService):
    name = "annotation"
    config_spec = ANNOTATION_CONFIG_SPEC
    stateful_menu_ids = AnnotationsMenuIds
    has_gui = True

    def __post_init__(self):
        self.__state = {}
        self.view.contentTextCtrl.Bind(wx.EVT_KEY_UP, self.onKeyUp, self.view.contentTextCtrl)
        self.view.Bind(
            self.view.contentTextCtrl.EVT_CARET,
            self.onCaretMoved,
            id=self.view.contentTextCtrl.GetId(),
        )
        self.view.add_load_handler(lambda red: wx.CallAfter(self._check_is_virtual, red))
        reader_book_loaded.connect(self.on_book_load, sender=self.reader)
        reader_book_unloaded.connect(self.on_book_unload, sender=self.reader)
        reader_page_changed.connect(self.comments_page_handler, sender=self.reader)
        reader_page_changed.connect(self.highlight_bookmarked_positions, sender=self.reader)
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
        selection = self.view.get_selection_range()
        if selection.start != selection.stop:
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
            bookmark_position = self.reader.storage_to_view_position(
                bookmark.position, bookmark.page_number
            )
            self.reader.go_to_page(bookmark.page_number, bookmark_position)
            if config.conf["annotation"]["select_bookmarked_line_on_jumping"]:
                self.view.select_text(*self.view.get_containing_line(bookmark_position))
            # Translators: spoken message when jumping to a bookmark
            msg = _("Bookmark")
            if bookmark.title:
                msg += f": {bookmark.title}"
            text_to_announce = (
                msg if config.conf["annotation"]["speak_bookmarks_on_jumping"] else None
            )
            reading_position_change.send(
                self.view,
                position=bookmark_position,
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
            start_pos, end_pos = (comment.start_pos, comment.end_pos)
            is_whole_line = (start_pos, end_pos) == (None, None)
            if is_whole_line:
                comment_position = self.reader.storage_to_view_position(
                    comment.position, comment.page_number
                )
                target_position = comment_position
                display_range = None
            else:
                display_range = self.reader.storage_to_view_range(
                    start_pos,
                    end_pos,
                    comment.page_number,
                )
                comment_position = display_range.stop
                target_position = comment_position
            self.reader.go_to_page(
                comment.page_number,
                target_position,
            )
            # We do not select whole line comments, See issue#332
            if not is_whole_line:
                self.view.select_text(display_range.start, display_range.stop)
            reading_position_change.send(
                self.view,
                position=target_position,
                # Translators: spoken message when jumping to a comment
                text_to_announce=_("Comment: {comment}").format(comment=comment.content),
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
            display_range = self.reader.storage_to_view_range(
                highlight.start_pos,
                highlight.end_pos,
                highlight.page_number,
            )
            self.reader.go_to_page(highlight.page_number, display_range.start)
            self.view.select_text(display_range.start, display_range.stop)
            reading_position_change.send(
                self.view,
                position=display_range.start,
                text_to_announce=_("Highlight"),
            )
            sounds.navigation.play()

    def onCaretMoved(self, event):
        # This method reacts every time the user moves the cursor.
        # The `event.Position` from wxPython is the REAL, physical position in the control.
        # All of our stored annotation positions (bookmarks, highlights) are "clean".
        # Therefore, we MUST convert the real `event.Position` into a `clean_position`
        # before doing any logical comparisons.
        event.Skip(True)
        if not self.reader.ready:
            return
        # Convert the real position from the event to a clean position.
        clean_position = (
            self.view.control_to_view_position(event.Position)
            if hasattr(self.view, "control_to_view_position")
            else event.Position - 1
        )
        if clean_position < 0:
            return
        evtdata = {}
        start, end = self.view.get_containing_line(clean_position)
        pos_range = range(start, end)
        for bookmark in Bookmarker(self.reader).get_for_page():
            bookmark_position = self.reader.storage_to_view_position(
                bookmark.position, bookmark.page_number
            )
            if bookmark_position in pos_range:
                evtdata["bookmark"] = True
                break
        for highlight in Quoter(self.reader).get_for_page():
            display_range = self.reader.storage_to_view_range(
                highlight.start_pos,
                highlight.end_pos,
                highlight.page_number,
            )
            if display_range.start <= clean_position < display_range.stop:
                evtdata["highlight"] = True
                break
            if display_range.start in pos_range:
                evtdata["line_contains_highlight"] = True
                break
        for comment in NoteTaker(self.reader).get_for_page():
            start_pos, end_pos = (comment.start_pos, comment.end_pos)
            if (start_pos, end_pos) != (None, None):
                display_range = self.reader.storage_to_view_range(
                    start_pos,
                    end_pos,
                    comment.page_number,
                )
                condition = display_range.start <= clean_position < display_range.stop
            else:
                condition = (
                    self.reader.storage_to_view_position(comment.position, comment.page_number)
                    in pos_range
                )
            if condition:
                evtdata["comment"] = True
        wx.CallAfter(self._process_caret_move, evtdata)

    def _process_caret_move(self, evtdata):
        if not any(evtdata.values()):
            return
        if config.conf["annotation"]["audable_indication_of_annotations_when_navigating_text"]:
            sounds.navigation.play()
        if config.conf["annotation"]["spoken_indication_of_annotations_when_navigating_text"]:
            to_speak = []
            if "bookmark" in evtdata:
                # Translators: spoken message indicating the presence of an annotation when the user navigates the text
                to_speak.append(_("Bookmarked"))
            if "highlight" in evtdata:
                # Translators: spoken message indicating the presence of an annotation when the user navigates the text
                to_speak.append(_("Highlighted"))
            elif "line_contains_highlight" in evtdata:
                # Translators: spoken message indicating the presence of an annotation when the user navigates the text
                to_speak.append(_("Line contains highlight"))
            if "comment" in evtdata:
                # Translators: Text that appears when only a comment is present
                comment_msg = _("Has comment")
                to_speak.append(comment_msg)
            speech.announce(" ".join(to_speak), False)

    def get_annotation(self, annotator_cls, *, foreword):
        if not (annotator := self.__state.get(annotator_cls.__name__)):
            annotator = self.__state.setdefault(annotator_cls.__name__, annotator_cls(self.reader))
        page_number = self.reader.current_page
        start = self.view.get_insertion_point()
        storage_start = self.reader.view_to_storage_position(start, page_number)
        if foreword:
            annot = annotator.get_first_after(page_number, storage_start)
        else:
            annot = annotator.get_first_before(page_number, storage_start)
        return annot

    def _check_is_virtual(self, sender):
        enable = not sender.document.uri.view_args.get("is_virtual", False)
        self.view.synchronise_menu(self.stateful_menu_ids, enable)

    def on_book_load(self, sender):
        current_page = sender.get_current_page_object()
        self.comments_page_handler(sender, current=current_page, prev=None)
        self.highlight_bookmarked_positions(sender, current=current_page, prev=None)
        self.highlight_highlighted_text(sender, current=current_page, prev=None)

    def on_book_unload(self, sender):
        self.__state.clear()

    @classmethod
    def comments_page_handler(cls, sender, current, prev):
        if not sender.ready:
            return
        comments = NoteTaker(sender)
        comments = comments.get_for_page()
        if comments.count():
            if config.conf["annotation"]["audable_indication_of_annotations_when_navigating_text"]:
                wx.CallLater(150, lambda: sounds.has_note.play())
        for comment in comments:
            comment_position = sender.storage_to_view_position(
                comment.position, comment.page_number
            )
            cls.style_comment(sender.view, comment_position)

    @classmethod
    def highlight_bookmarked_positions(cls, sender, current, prev):
        if not config.conf["annotation"]["use_visuals"]:
            return
        if not sender.ready:
            return
        bookmarks = Bookmarker(sender).get_for_page()
        if not bookmarks.count():
            return
        for bookmark in bookmarks:
            bookmark_position = sender.storage_to_view_position(
                bookmark.position, bookmark.page_number
            )
            cls.style_bookmark(sender.view, bookmark_position)

    @classmethod
    def highlight_highlighted_text(cls, sender, current, prev):
        if not config.conf["annotation"]["use_visuals"]:
            return
        if not sender.ready:
            return
        quoter = Quoter(sender)
        for_page = quoter.get_for_page()
        if not for_page.count():
            return
        for quote in for_page:
            display_range = sender.storage_to_view_range(
                quote.start_pos,
                quote.end_pos,
                quote.page_number,
            )
            cls.style_highlight(sender.view, display_range.start, display_range.stop)

    @staticmethod
    @gui_thread_safe
    def style_bookmark(view, position, enable=True):
        # This method applies a visual style (underline) to a line.
        # The input `position` is a clean index.
        # The final call to `.SetStyle()` MUST use real, offset-adjusted positions.
        if not config.conf["annotation"]["use_visuals"]:
            return
        # `get_containing_line` is a gatekeeper and correctly returns a clean range.
        start, end = view.get_containing_line(position)
        # We need a new TextAttr object to avoid modifying a shared default style.
        new_attr = wx.TextAttr()
        # We must get the existing style from the REAL position to preserve other attributes.
        real_start = (
            view.view_to_control_position(start)
            if hasattr(view, "view_to_control_position")
            else start + 1
        )
        real_end = (
            view.view_to_control_position(end)
            if hasattr(view, "view_to_control_position")
            else end + 1
        )
        view.contentTextCtrl.GetStyle(real_start, new_attr)
        new_attr.SetFontUnderlined(enable)
        # We must apply the new style to the REAL, offset positions.
        view.contentTextCtrl.SetStyle(real_start, real_end, new_attr)

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
