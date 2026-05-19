
from enum import IntEnum

import wx

from bookworm import speech
from bookworm.gui.settings import SettingsPanel
from bookworm.logger import logger
from bookworm.structured_text import CURRENT_POSITION_MODEL_VERSION

from .annotation_dialogs import (
    BookmarksViewer,
    CommentsDialog,
    GenericAnnotationWithContentDialog,
    QuotesDialog,
)
from .annotator import Bookmarker, NoteTaker, Quoter

log = logger.getChild(__name__)


class AnnotationSettingsPanel(SettingsPanel):
    config_section = "annotation"

    def addControls(self):
        # Translators: the title of a group of controls in the settings dialog
        InteractionBox = self.make_static_box(_("When navigating text"))
        wx.CheckBox(
            InteractionBox,
            -1,
            # Translators: the label of a checkbox
            _("Play a sound to indicate the presence of annotations"),
            name="annotation.audable_indication_of_annotations_when_navigating_text",
        )
        wx.CheckBox(
            InteractionBox,
            -1,
            # Translators: the label of a checkbox
            _("Speak a message to indicate the presence of annotations"),
            name="annotation.spoken_indication_of_annotations_when_navigating_text",
        )
        # Translators: the title of a group of controls in the settings dialog
        UIBox = self.make_static_box(_("Miscellaneous settings"))
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Speak the bookmark when jumping"),
            name="annotation.speak_bookmarks_on_jumping",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Select the bookmarked line when jumping"),
            name="annotation.select_bookmarked_line_on_jumping",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Use visual styles to indicate annotations"),
            name="annotation.use_visuals",
        )


class AnnotationsMenuIds(IntEnum):
    addBookmark = 241
    addNamedBookmark = 242
    addNote = 243
    quoteSelection = 244
    viewBookmarks = 245


class StatelessAnnotationsMenuIds(IntEnum):
    viewNotes = 246
    viewQuotes = 247


ANNOTATIONS_KEYBOARD_SHORTCUTS = {
    AnnotationsMenuIds.addBookmark: "Ctrl-B",
    AnnotationsMenuIds.addNamedBookmark: "Ctrl-Shift-B",
    AnnotationsMenuIds.addNote: "Ctrl-M",
    AnnotationsMenuIds.quoteSelection: "Ctrl-H",
}


class AnnotationMenu(wx.Menu):
    """Annotation menu."""

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.view = service.view
        self.reader = service.reader

        # Add menu items
        self.Append(
            AnnotationsMenuIds.addBookmark,
            # Translators: the label of an item in the application menubar
            _("Add &Bookmark\tCtrl-B"),
            # Translators: the help text of an item in the application menubar
            _("Add a bookmark at the current position"),
        )
        self.Append(
            AnnotationsMenuIds.addNamedBookmark,
            # Translators: the label of an item in the application menubar
            _("Add &Named Bookmark...\tCtrl-Shift-B"),
            # Translators: the help text of an item in the application menubar
            _("Add a named bookmark at the current position"),
        )
        self.Append(
            AnnotationsMenuIds.addNote,
            # Translators: the label of an item in the application menubar
            _("Add Co&mment...\tCtrl-M"),
            # Translators: the help text of an item in the application menubar
            _("Add a comment at the current position"),
        )
        self.Append(
            AnnotationsMenuIds.quoteSelection,
            # Translators: the label of an item in the application menubar
            _("&Highlight Selection\tCtrl-H"),
            # Translators: the help text of an item in the application menubar
            _("Highlight selected text and save it."),
        )
        self.Append(
            AnnotationsMenuIds.viewBookmarks,
            # Translators: the label of an item in the application menubar
            _("Saved &Bookmarks..."),
            # Translators: the help text of an item in the application menubar
            _("View added bookmarks"),
        )
        self.Append(
            StatelessAnnotationsMenuIds.viewNotes,
            # Translators: the label of an item in the application menubar
            _("Saved Co&mments..."),
            # Translators: the help text of an item in the application menubar
            _("View, edit, and remove comments."),
        )
        self.Append(
            StatelessAnnotationsMenuIds.viewQuotes,
            # Translators: the label of an item in the application menubar
            _("Saved &Highlights..."),
            # Translators: the help text of an item in the application menubar
            _("View saved highlights."),
        )

        # Translators: the label of an item in the application menubar

        # EventHandlers
        self.view.Bind(wx.EVT_MENU, self.onAddBookmark, id=AnnotationsMenuIds.addBookmark)
        self.view.Bind(wx.EVT_MENU, self.onAddNamedBookmark, id=AnnotationsMenuIds.addNamedBookmark)
        self.view.Bind(wx.EVT_MENU, self.onAddNote, id=AnnotationsMenuIds.addNote)
        self.view.Bind(wx.EVT_MENU, self.onQuoteSelection, id=AnnotationsMenuIds.quoteSelection)
        self.view.Bind(wx.EVT_MENU, self.onViewBookmarks, id=AnnotationsMenuIds.viewBookmarks)
        self.view.Bind(wx.EVT_MENU, self.onViewNotes, id=StatelessAnnotationsMenuIds.viewNotes)
        self.view.Bind(wx.EVT_MENU, self.onViewQuotes, id=StatelessAnnotationsMenuIds.viewQuotes)

    def _add_bookmark(self, name=""):
        bookmarker = Bookmarker(self.reader)
        insertionPoint = self.view.get_insertion_point()
        storage_insertion_point = self.reader.view_to_storage_position(insertionPoint)
        current_lino = self.view.get_line_number(insertionPoint)
        count = 0
        for bkm in bookmarker.get_for_page(self.reader.current_page):
            bookmark_position = self.reader.storage_to_view_position(bkm.position, bkm.page_number)
            lino = self.view.get_line_number(bookmark_position)
            if lino == current_lino:
                count += 1
                bookmarker.delete(bkm.id)
                self.service.style_bookmark(self.view, bookmark_position, enable=False)
        if count and not name:
            return speech.announce(_("Bookmark removed"))
        Bookmarker(self.reader).create(title=name, position=storage_insertion_point)
        # Translators: spoken message
        speech.announce(_("Bookmark Added"))
        self.service.style_bookmark(self.view, insertionPoint)

    def onAddBookmark(self, event):
        self._add_bookmark()

    def onAddNamedBookmark(self, event):
        bookmark_name = self.view.get_text_from_user(
            # Translators: title of a dialog
            _("Add Named Bookmark"),
            # Translators: label of a text entry
            _("Bookmark name:"),
        )
        if bookmark_name:
            self._add_bookmark(bookmark_name)

    def onAddNote(self, event):
        _with_tags = wx.GetKeyState(wx.WXK_SHIFT)
        insertionPoint = self.view.get_insertion_point()
        storage_insertion_point = self.reader.view_to_storage_position(insertionPoint)
        selection_range = self.view.get_selection_range()
        start_pos, end_pos = selection_range.start, selection_range.stop
        # if start_pos and end_pos are equal, there is no selection
        # see: https://docs.wxpython.org/wx.TextEntry.html#wx.TextEntry.GetSelection
        storage_start_pos = None
        storage_end_pos = None
        if start_pos == end_pos:
            start_pos, end_pos = (None, None)
        else:
            storage_start_pos, storage_end_pos = self.reader.view_to_storage_range(
                start_pos,
                end_pos,
                self.reader.current_page,
            ).astuple()
        comments = NoteTaker(self.reader)
        if comments.overlaps(
            storage_start_pos,
            storage_end_pos,
            self.reader.current_page,
            storage_insertion_point,
        ):
            return self.view.notify_user(
                _("Error"),
                # Translator: Message obtained whenever another note is overlapping the selected position
                _("Another note is currently overlapping the selected position."),
            )
        comment_text = self.view.get_text_from_user(
            # Translators: the title of a dialog to add a comment
            _("New Comment"),
            # Translators: the label of an edit field to enter a comment
            _("Comment:"),
            style=wx.OK | wx.CANCEL | wx.TE_MULTILINE | wx.CENTER,
        )
        if not comment_text:
            return None
        note = comments.create(
            title="",
            content=comment_text,
            position=storage_insertion_point,
            start_pos=storage_start_pos,
            end_pos=storage_end_pos,
        )

        self.service.style_comment(self.view, insertionPoint)
        if _with_tags:
            # add tags
            tags_text = self.view.get_text_from_user(
                # Translators: title of a dialog
                _("Tag Comment"),
                # Translators: label of a text entry
                _("Tags:"),
            )
            if tags_text:
                for tag in tags_text.split():
                    note.tags.append(tag.strip())
                NoteTaker.model.session.commit()

    def onQuoteSelection(self, event):
        _with_tags = wx.GetKeyState(wx.WXK_SHIFT)
        quoter = Quoter(self.reader)
        x, y = self.view.get_selection_range()
        if x == y:
            return speech.announce(_("No selection"))
        selected_text = self.view.get_text_by_range(x, y)
        storage_range = self.reader.view_to_storage_range(x, y, self.reader.current_page)
        for q in quoter.get_for_page():
            q_range = self.reader.storage_to_view_range(q.start_pos, q.end_pos, q.page_number)
            if (q_range.start == x) and (q_range.stop == y):
                quoter.delete(q.id)
                self.service.style_highlight(self.view, x, y, enable=False)
                # Translators: spoken message
                return speech.announce(_("Highlight removed"))
            if (q_range.start < x) and (q_range.stop > y):
                # Translators: spoken message
                speech.announce(_("Already highlighted"))
                return wx.Bell()
            if (q_range.start <= x < q_range.stop) or (q_range.start <= y < q_range.stop):
                if not (q_range.start <= x < q_range.stop):
                    q.start_pos = self.reader.view_to_storage_position(
                        x, q.page_number, affinity="before"
                    )
                    q.position_version = CURRENT_POSITION_MODEL_VERSION
                    q.session.commit()
                    self.service.style_highlight(self.view, x, q_range.stop)
                    return speech.announce(_("Highlight extended"))
                if not (q_range.start <= y < q_range.stop):
                    q.end_pos = self.reader.view_to_storage_range(
                        q_range.start,
                        y,
                        q.page_number,
                    ).stop
                    q.position_version = CURRENT_POSITION_MODEL_VERSION
                    q.session.commit()
                    self.service.style_highlight(self.view, q_range.start, y)
                    # Translators: spoken message
                    return speech.announce(_("Highlight extended"))
        quote = quoter.create(
            title="",
            content=selected_text,
            start_pos=storage_range.start,
            end_pos=storage_range.stop,
        )
        # Translators: spoken message
        speech.announce(_("Selection highlighted"))
        self.service.style_highlight(self.view, x, y)
        if _with_tags:
            # add tags
            tags_text = self.view.get_text_from_user(
                # Translators: title of a dialog
                _("Tag Highlight"),
                # Translators: label of a text entry
                _("Tags:"),
            )
            if tags_text:
                for tag in tags_text.split():
                    quote.tags.append(tag.strip())
                Quoter.model.session.commit()

    def onViewBookmarks(self, event):
        with BookmarksViewer(
            parent=self.view,
            reader=self.reader,
            annotator=Bookmarker,
            # Translators: the title of a dialog to view bookmarks
            title=_("Bookmarks | {book}").format(book=self.reader.current_book.title),
        ) as dlg:
            dlg.ShowModal()

    def onViewNotes(self, event):
        Dialog = CommentsDialog if self.reader.ready else GenericAnnotationWithContentDialog
        with Dialog(
            parent=self.view,
            title=_("Comments"),
            reader=self.reader,
            annotator_cls=NoteTaker,
            can_edit=True,
        ) as dlg:
            dlg.ShowModal()

    def onViewQuotes(self, event):
        Dialog = QuotesDialog if self.reader.ready else GenericAnnotationWithContentDialog
        with Dialog(
            parent=self.view,
            title=_("Highlights"),
            reader=self.reader,
            annotator_cls=Quoter,
        ) as dlg:
            dlg.ShowModal()
