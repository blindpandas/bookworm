# coding: utf-8

import math
import time
import webbrowser
from contextlib import contextmanager
from functools import partial
from pathlib import Path

import wx

from bookworm.text_to_speech import TextToSpeechService
from bookworm import app, config, speech
from bookworm import typehints as t
from bookworm.concurrency import CancellationToken, threaded_worker
from bookworm.document import (
    ArchiveContainsMultipleDocuments,
    ArchiveContainsNoDocumentsError,
    DocumentRestrictedError,
    DummyDocument,
)
from bookworm.gui.browseable_message import browseable_message
from bookworm.gui.components import AsyncSnakDialog, TocTreeManager
from bookworm.gui.contentview_ctrl import ContentViewCtrl
from bookworm.logger import logger
from bookworm.paths import app_path, fonts_path
from bookworm.reader import (
    DecryptionRequired,
    EBookReader,
    ReaderError,
    ResourceDoesNotExist,
    UnsupportedDocumentError,
    UriResolver,
)
from bookworm.resources import app_icons, sounds
from bookworm.runtime import keep_awake
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reading_position_change,
)
from bookworm.structured_text import SEMANTIC_ELEMENT_OUTPUT_OPTIONS, Style, TextRange
from bookworm.utils import gui_thread_safe

from . import recents_manager
from .menubar import BookRelatedMenuIds, MenubarProvider
from .navigation import NavigationProvider
from .state import StateProvider

log = logger.getChild(__name__)

# Style to wx TextCtrl Styles
STYLE_TO_WX_TEXT_ATTR_STYLES = {
    Style.BOLD: (wx.TextAttr.SetFontWeight, (wx.FONTWEIGHT_BOLD,)),
    Style.ITALIC: (wx.TextAttr.SetFontStyle, (wx.FONTSTYLE_ITALIC,)),
    Style.MONOSPACED: (wx.TextAttr.SetFontStyle, (wx.FONTSTYLE_ITALIC,)),
    Style.UNDERLINED: (wx.TextAttr.SetFontUnderlined, (True,)),
    Style.STRIKETHROUGH: (
        wx.TextAttr.SetTextEffects,
        (wx.TEXT_ATTR_EFFECT_STRIKETHROUGH,),
    ),
    Style.SUPERSCRIPT: (wx.TextAttr.SetTextEffects, (wx.TEXT_ATTR_EFFECT_SUPERSCRIPT,)),
    Style.SUBSCRIPT: (wx.TextAttr.SetTextEffects, (wx.TEXT_ATTR_EFFECT_SUBSCRIPT,)),
    Style.HIGHLIGHTED: (wx.TextAttr.SetBackgroundColour, (wx.YELLOW,)),
    Style.DISPLAY_1: (wx.TextAttr.SetFontWeight, (800,)),
    Style.DISPLAY_2: (wx.TextAttr.SetFontWeight, (600,)),
    Style.DISPLAY_3: (wx.TextAttr.SetFontWeight, (400,)),
    Style.DISPLAY_4: (wx.TextAttr.SetFontWeight, (200,)),
}

TEXT_CTRL_OFFSET = 1


class ResourceLoader:
    """Loads a document into the view."""

    def __init__(self, view, uri, callback=None):
        self.view = view
        self.callback = callback
        self._cancellation_token = CancellationToken()
        self.init_resolver(uri)

    def init_resolver(self, uri):
        try:
            resolver = UriResolver(uri)
        except ReaderError as e:
            log.exception(f"Failed to resolve document uri: {uri}", exc_info=True)
            self.view.notify_user(
                _("Failed to open document"),
                _(
                    "The document you are trying to open could not be opened in Bookworm."
                ),
                icon=wx.ICON_ERROR,
            )
            return
        if not resolver.should_read_async():
            doc = self.resolve_document(resolver.read_document, uri)
        else:
            AsyncSnakDialog(
                task=partial(resolver.read_document),
                done_callback=lambda fut: self.resolve_document(fut.result, uri),
                dismiss_callback=lambda: self._cancellation_token.request_cancellation()
                or True,
                message=_("Opening document, please wait..."),
                parent=self.view,
            )

    def resolve_document(self, resolve_doc_func, uri):
        _last_exception = None
        try:
            doc = resolve_doc_func()
            if doc is not None:
                self.load(doc)
        except DecryptionRequired:
            self.view.decrypt_document(uri)
        except ResourceDoesNotExist as e:
            _last_exception = e
            log.exception("Failed to open file. File does not exist", exc_info=True)
            wx.CallAfter(
                self.view.notify_user,
                # Translators: the title of an error message
                _("Document not found"),
                # Translators: the content of an error message
                _("Could not open Document.\nThe document does not exist."),
                icon=wx.ICON_ERROR,
            )
        except DocumentRestrictedError as e:
            _last_exception = e
            log.exception(
                "Failed to open document. The document is restricted by the author.",
                exc_info=True,
            )
            wx.CallAfter(
                self.view.notify_user,
                # Translators: the title of an error message
                _("Document Restricted"),
                # Translators: the content of an error message
                _(
                    "Could not open Document.\nThe document is restricted by the publisher."
                ),
                icon=wx.ICON_ERROR,
            )
        except UnsupportedDocumentError as e:
            _last_exception = e
            log.exception("Unsupported file format", exc_info=True)
            wx.CallAfter(
                self.view.notify_user,
                # Translators: the title of a message shown
                # when the format of the e-book is not supported
                _("Unsupported Document Format"),
                # Translators: the content of a message shown
                # when the format of the e-book is not supported
                _("The format of the given document is not supported by Bookworm."),
                icon=wx.ICON_WARNING,
            )
        except ArchiveContainsNoDocumentsError as e:
            _last_exception = e
            log.exception("Archive contains no documents", exc_info=True)
            wx.CallAfter(
                self.view.notify_user,
                # Translators: the title of an error message
                _("Archive contains no documents"),
                # Translators: the content of an error message
                _(
                    "Bookworm cannot open this archive file.\nThe archive contains no documents."
                ),
                icon=wx.ICON_ERROR,
            )
        except ArchiveContainsMultipleDocuments as e:
            log.info("Archive contains multiple documents")
            dlg = wx.SingleChoiceDialog(
                self.view,
                _("Documents"),
                _("Multiple documents found"),
                e.args[0],
                wx.CHOICEDLG_STYLE,
            )
            if dlg.ShowModal() == wx.ID_OK:
                member = dlg.GetStringSelection()
                new_uri = uri.create_copy(view_args={"member": member})
                self.view.open_uri(new_uri)
        except ReaderError as e:
            _last_exception = e
            log.exception("Unsupported file format", exc_info=True)
            wx.CallAfter(
                self.view.notify_user,
                # Translators: the title of an error message
                _("Error Opening Document"),
                # Translators: the content of an error message
                _(
                    "Could not open file\n."
                    "Either the file  has been damaged during download, "
                    "or it has been corrupted in some other way."
                ),
                icon=wx.ICON_ERROR,
            )
        except Exception as e:
            _last_exception = e
            log.exception("Unknown error occurred", exc_info=True)
            wx.CallAfter(
                self.view.notify_user,
                # Translators: the title of an error message
                _("Error Openning Document"),
                # Translators: the content of an error message
                _(
                    "Could not open document.\n"
                    "An unknown error occurred while loading the file."
                ),
                icon=wx.ICON_ERROR,
            )
        finally:
            if _last_exception is not None:
                wx.CallAfter(self.view.unloadCurrentEbook)
                if uri.view_args.get("from_list"):
                    retval = wx.MessageBox(
                        # Translators: content of a message
                        _(
                            "Failed to open document.\nWould you like to remove its entry from the 'recent documents' and 'pinned documents' lists?"
                        ),
                        # Translators: title of a message box
                        _("Remove from lists?"),
                        style=wx.YES_NO | wx.ICON_WARNING,
                    )
                    if retval == wx.YES:
                        recents_manager.remove_from_recents(uri)
                        recents_manager.remove_from_pinned(uri)
                        self.view.fileMenu.populate_recent_file_list()
                        self.view.fileMenu.populate_pinned_documents_list()
                if app.debug:
                    raise _last_exception

    def load(self, document):
        if (document is None) or (self._cancellation_token.is_cancellation_requested()):
            return
        self.view.load_document(document)
        if self.callback is not None:
            self.callback()


class BookViewerWindow(wx.Frame, MenubarProvider, StateProvider):
    """The book viewer window."""

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, name="main_window")
        self.wx_key_map = {
            wx.WXK_MEDIA_PLAY_PAUSE: "play_pause",
            wx.WXK_MEDIA_NEXT_TRACK: "next",
            wx.WXK_MEDIA_PREV_TRACK: "prev",
        }
        self.setFrameIcon()

        self.reader = EBookReader(self)
        self._book_loaded_handlers = []
        self.createControls()

        self.toolbar = self.CreateToolBar()
        self.toolbar.SetWindowStyle(
            wx.TB_FLAT | wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_TEXT
        )
        self.statusBar = self.CreateStatusBar()
        self._nav_provider = NavigationProvider(
            ctrl=self.contentTextCtrl,
            reader=self.reader,
            zoom_callback=self.onTextCtrlZoom,
            view=self,
        )

        # Used in continuous reading feature
        self._last_page_turn_time = 0

        # Bind Events
        self.tocTreeCtrl.Bind(wx.EVT_SET_FOCUS, self.onTocTreeFocus, self.tocTreeCtrl)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onTOCItemClick, self.tocTreeCtrl)
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(-1), id=wx.ID_PREVIEW_ZOOM_OUT
        )
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(1), id=wx.ID_PREVIEW_ZOOM_IN
        )
        self.Bind(
            self.contentTextCtrl.EVT_CARET,
            self.onCaretMoved,
            id=self.contentTextCtrl.GetId(),
        )
        self.Bind(
            wx.EVT_SLIDER,
            self.onSliderValueChanged,
            id=self.readingProgressSlider.GetId(),
        )

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press_local)

        self.toc_tree_manager = TocTreeManager(self.tocTreeCtrl)
        # Set status bar text
        # Translators: the text of the status bar when no book is currently open.
        # It is being used also as a label for the page content text area when no book is opened.
        self._no_open_book_status = _("Press (Ctrl + O) to open a document")
        self._has_text_zoom = False
        self.__latest_structured_navigation_position = None
        self.set_status(self._no_open_book_status)
        StateProvider.__init__(self)
        MenubarProvider.__init__(self)

    def on_key_press_local(self, event):
        if config.conf["reading"]["enable_global_media_keys"]:
            event.Skip()
            return

        keycode = event.GetKeyCode()
        key_name = self.wx_key_map.get(keycode)

        if key_name:
            tts_service = wx.GetApp().service_handler.get_service("text_to_speech")
            if not tts_service:
                return

            if key_name == "play_pause":
                tts_service.pause_or_resume()
            elif key_name == "next":
                tts_service.fastforward()
            elif key_name == "prev":
                tts_service.rewind()
        else:
            event.Skip()
    
    def createControls(self):
        # Now create the Panel to put the other controls on.
        rect = wx.GetClientDisplayRect()
        panel = wx.Panel(self, size=(rect.width * 0.8, rect.height * 0.75))

        # Create the book reader controls
        # Translators: the label of the table-of-contents tree
        tocTreeLabel = wx.StaticText(panel, -1, _("Table of Contents"))
        self.tocTreeCtrl = wx.TreeCtrl(
            panel,
            size=(280, 160),
            style=wx.TR_HAS_BUTTONS
            | wx.TR_TWIST_BUTTONS
            | wx.TR_LINES_AT_ROOT
            | wx.TR_FULL_ROW_HIGHLIGHT
            | wx.TR_SINGLE
            | wx.TR_ROW_LINES,
            name="toc_tree",
        )
        self.contentTextCtrl = ContentViewCtrl(
            panel,
            # Translators: the label of the text area which shows the
            # content of the current page
            label=_("Content"),
            size=(200, 160),
            name="content_view",
        )
        self.set_text_view_margins()
        # Translators: label for the reading progress slider
        readingProgressLabel = wx.StaticText(
            panel, -1, _("Reading progress percentage")
        )
        self.readingProgressSlider = wx.Slider(
            panel, -1, style=wx.SL_HORIZONTAL  # | wx.SL_LABELS
        )
        self.readingProgressSlider.SetTick(5)

        # Use a sizer to layout the controls, stacked horizontally and with
        # a 10 pixel border around each
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        lftSizer = wx.BoxSizer(wx.VERTICAL)
        rgtSizer = wx.BoxSizer(wx.VERTICAL)
        rgtBottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        lftSizer.Add(tocTreeLabel, 0, wx.ALL, 5)
        lftSizer.Add(self.tocTreeCtrl, 1, wx.ALL, 5)
        rgtSizer.Add(self.contentTextCtrl.panel, 1, wx.EXPAND | wx.ALL, 3)
        rgtBottomSizer.Add(readingProgressLabel, 1, wx.ALL, 1)
        rgtBottomSizer.Add(self.readingProgressSlider, 1, wx.EXPAND | wx.ALL, 1)
        rgtSizer.Add(rgtBottomSizer, 0, wx.ALL | wx.EXPAND, 4)
        mainSizer.Add(lftSizer, 0, wx.ALL | wx.EXPAND, 10)
        mainSizer.Add(rgtSizer, 1, wx.ALL | wx.EXPAND, 10)
        panel.SetSizer(mainSizer)
        panel.Layout()

        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer()
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        self.SetSize(wx.Size(1300, 750))
        self.CenterOnScreen(wx.BOTH)

    def finalize_gui_creation(self):
        opendyslexic_font_filename = fonts_path(
            "opendyslexic", "OpenDyslexic-Regular.ttf"
        )
        wx.Font.AddPrivateFont(str(opendyslexic_font_filename))
        self.set_content_view_font()
        self.add_tools()
        self.toolbar.Realize()
        # Process services menubar
        for retval in wx.GetApp().service_handler.process_menubar(self.menuBar):
            if retval is None:
                continue
            menu_order, menu_object, menu_label = retval
            self.registerMenu(menu_order, menu_object, menu_label)
        self.doAddMenus()
        self.SetMenuBar(self.menuBar)
        # Set accelerators for the menu items
        self._set_menu_accelerators()
        if not config.conf["appearance"]["show_application_toolbar"]:
            self.toolbar.Hide()
        if config.conf["appearance"]["start_maximized"]:
            self.Maximize()
        # XXX sent explicitly to disable items upon startup
        reader_book_unloaded.send(self.reader)

    def set_content_view_font(self):
        configured_text_style = self.get_content_view_text_style()
        self.contentTextCtrl.SetStyle(
            0, self.contentTextCtrl.GetLastPosition(), configured_text_style
        )
        self.contentTextCtrl.SetDefaultStyle(configured_text_style)

    def get_content_view_text_style(self, *, font_size=None):
        finfo = wx.FontInfo().FaceName(config.conf["appearance"]["font_facename"])
        configured_font = wx.Font(finfo)
        font_point_size = (
            font_size
            if font_size is not None
            else config.conf["appearance"]["font_point_size"]
        )
        configured_font.SetPointSize(font_point_size)
        if config.conf["appearance"]["use_bold_font"]:
            configured_font.SetWeight(wx.FONTWEIGHT_BOLD)
        base_text_style = self.contentTextCtrl.GetDefaultStyle()
        base_text_style.SetFont(configured_font)
        return base_text_style

    def add_tools(self):
        tsize = (16, 16)
        self.toolbar.SetToolBitmapSize(tsize)
        tool_info = [
            # Translators: the label of a button in the application toolbar
            (0, "open", _("Open"), wx.ID_OPEN),
            (1, "", "", None),
            # Translators: the label of a button in the application toolbar
            (10, "search", _("Search"), wx.ID_FIND),
            # Translators: the label of a button in the application toolbar
            (20, "reading_mode", _("Mode"), BookRelatedMenuIds.changeReadingMode),
            (32, "", "", None),
            # Translators: the label of a button in the application toolbar
            (60, "zoom_out", _("Small"), wx.ID_PREVIEW_ZOOM_OUT),
            # Translators: the label of a button in the application toolbar
            (70, "zoom_in", _("Big"), wx.ID_PREVIEW_ZOOM_IN),
            (71, "", "", None),
        ]
        tool_info.extend(wx.GetApp().service_handler.get_toolbar_items())
        tool_info.sort()
        for pos, imagename, label, ident in tool_info:
            if ident is None:
                self.toolbar.AddSeparator()
                continue
            image = getattr(app_icons, imagename).GetBitmap()
            # Add toolbar item
            self.toolbar.AddTool(ident, label, image)

    def add_load_handler(self, func):
        self._book_loaded_handlers.append(func)

    def invoke_load_handlers(self):
        for func in self._book_loaded_handlers:
            func(self.reader)

    def default_book_loaded_callback(self):
        if self.contentTextCtrl.HasFocus():
            self.tocTreeCtrl.SetFocus()

    def load_document(self, document) -> bool:
        with reader_book_loaded.connected_to(
            self.book_loaded_handler, sender=self.reader
        ):
            self.reader.set_document(document)

    @gui_thread_safe
    def book_loaded_handler(self, sender):
        self.invoke_load_handlers()

    def open_uri(self, uri, callback=None):
        self.unloadCurrentEbook()
        ResourceLoader(
            self, uri, callback=callback or self.default_book_loaded_callback
        )

    def decrypt_document(self, uri):
        if uri.view_args.get("n_attempts"):
            self.notify_user(
                # Translators: title of a message telling the user that they entered an incorrect
                # password for opening the book
                _("Incorrect Password"),
                # Translators: content of a message telling the user that they entered an incorrect
                # password for opening the book
                _(
                    "The password you provided is incorrect.\n"
                    "Please try again with the correct password."
                ),
                icon=wx.ICON_ERROR,
            )
        retval = self.get_password_from_user()
        if retval is None:
            return
        else:
            new_uri = uri.create_copy(
                view_args={"decryption_key": retval, "n_attempts": "1"}
            )
            return self.open_uri(new_uri)

    def open_document(self, document):
        self.unloadCurrentEbook()
        self.reader.set_document(document)

    def set_content(self, content):
        self.contentTextCtrl.Freeze()
        if self._has_text_zoom:
            current_style = wx.TextAttr(self.contentTextCtrl.GetDefaultStyle())
            self.contentTextCtrl.GetStyle(0, current_style)
            current_font_size = current_style.Font.GetPointSize()
        else:
            current_font_size = None
        self.contentTextCtrl.SetValue("\n\n")
        self.contentTextCtrl.SetInsertionPoint(1)
        self.contentTextCtrl.SetDefaultStyle(
            self.get_content_view_text_style(font_size=current_font_size)
        )
        self.contentTextCtrl.WriteText(content)
        self.set_insertion_point(0)
        self.contentTextCtrl.Thaw()

    def set_title(self, title):
        self.SetTitle(title)

    def set_status(self, text, statusbar_only=False, *args, **kwargs):
        super().SetStatusText(text, *args, **kwargs)
        if not statusbar_only:
            self.contentTextCtrl.SetControlLabel(text)

    def unloadCurrentEbook(self):
        true_unload_opt = (
            not isinstance(self.reader.document, DummyDocument)
            and self.reader.document is not None
        )
        self.readingProgressSlider.SetValue(0)
        self.reader.unload()
        self.clear_toc_tree()
        self.set_title(app.display_name)
        self.set_content("")
        if self._has_text_zoom:
            self.onTextCtrlZoom(0, announce=False)
        self.clear_highlight()
        self.set_status(self._no_open_book_status)
        if true_unload_opt:
            sounds.close_document.play()
            # Translators: spoken message when the document has been closed
            speech.announce(_("Document closed."))

    def add_toc_tree(self, tree):
        self.toc_tree_manager.build_tree(tree)

    def tocTreeSetSelection(self, item):
        self.toc_tree_manager.set_selection(item)

    def clear_toc_tree(self):
        self.toc_tree_manager.clear_tree()

    def set_state_on_section_change(self, current):
        self.tocTreeSetSelection(current)
        is_single_page_doc = self.reader.document.is_single_page_document()
        if is_single_page_doc:
            target_pos = self.get_containing_line(current.text_range.start + 1)[0]
            self.set_insertion_point(target_pos)
        if is_single_page_doc:
            sounds.navigation.play()

    def update_reading_progress(self):
        self.readingProgressSlider.Enable(
            config.conf["general"]["show_reading_progress_percentage"]
        )
        if self.reader.document.is_single_page_document():
            char_count = self.get_last_position()
            if char_count == 0:
                return
            current_ratio = self.get_insertion_point() / char_count
        else:
            current_ratio = (self.reader.current_page + 1) / len(self.reader.document)
        percentage_ratio = math.ceil(current_ratio * 100)
        wx.CallAfter(self.readingProgressSlider.SetValue, percentage_ratio)
        percentage_display = app.current_language.format_percentage(
            percentage_ratio / 100
        )
        # Translators: text of reading progress shown in the status bar
        status_text = _("{percentage} completed").format(percentage=percentage_display)
        if existing_status := self.get_statusbar_text():
            status_text = f"{status_text} {chr(0x00B7)} {existing_status}"
        wx.CallAfter(self.set_status, status_text, statusbar_only=True)

    def onCaretMoved(self, event):
        event.Skip(True)
        if not self.reader.ready:
            return
        threaded_worker.submit(self._after_caret_moved)
        if (
            config.conf["general"]["use_continuous_reading"]
            and event.Position == self.contentTextCtrl.GetLastPosition()
        ):
            if (time.monotonic() - self._last_page_turn_time) <= 0.75:
                return
            self.reader.go_to_next()
            self._last_page_turn_time = time.monotonic()
        wx.CallAfter(keep_awake)

    def _after_caret_moved(self):
        try:
            self.reader.save_current_position()
        except:
            log.exception("Failed to save current position", exc_info=True)
        if self.reader.document.is_single_page_document():
            self.update_reading_progress()

    def onTocTreeFocus(self, event):
        event.Skip(True)
        if not self.reader.document.is_single_page_document():
            return
        condition = (
            self.reader.ready
            and self.reader.active_section is not None
            and self.get_insertion_point() not in self.reader.active_section.text_range
        )
        if condition:
            self.reader.active_section = self.reader.document.get_section_at_position(
                self.get_insertion_point()
            )
            event.GetEventObject().SetFocus()

    def onTOCItemClick(self, event):
        selectedItem = event.GetItem()
        self.reader.active_section = self.tocTreeCtrl.GetItemData(selectedItem)
        self.reader.go_to_first_of_section()
        self.contentTextCtrl.SetFocus()

    def set_state_on_page_change(self, page):
        self.set_content(page.get_text())
        if config.conf["general"]["play_pagination_sound"]:
            sounds.pagination.play()
        status_text = self.get_statusbar_text()
        self.set_status(status_text)
        if self.reader.document.is_single_page_document():
            # Translators: label of content text control when the currently opened
            # document is a single page document
            self.contentTextCtrl.SetControlLabel(_("Document content"))
        wx.CallAfter(self.update_reading_progress)

    def navigate_to_structural_element(self, element_type, forward):
        if not self.reader.ready:
            wx.Bell()
            return
        current_insertion_point = self.get_insertion_point()
        pos = self.reader.get_semantic_element(
            element_type,
            forward,
            current_insertion_point,
        )
        if pos is not None:
            ((start, stop), actual_element_type) = pos
            pos_info = (current_insertion_point, pos)
            if self.__latest_structured_navigation_position == pos_info:
                self.set_insertion_point(stop)
                return self.navigate_to_structural_element(element_type, forward)
            self.__latest_structured_navigation_position = pos_info
            (
                element_label,
                should_speak_whole_text,
                move_to_start_of_line,
            ) = SEMANTIC_ELEMENT_OUTPUT_OPTIONS[actual_element_type]
            text_start, text_stop = (
                self.get_containing_line(start + 1)
                if should_speak_whole_text
                else (start, stop)
            )
            text = self.get_text_by_range(text_start, text_stop)
            msg = _("{text}: {item_type}").format(text=text, item_type=_(element_label))
            target_position = (
                start
                if not move_to_start_of_line
                else self.get_containing_line(stop - 1)[0]
            )
            self.set_insertion_point(target_position)
            speech.announce(msg, True)
            sounds.structured_navigation.play()
            reading_position_change.send(
                self,
                position=start,
                tts_speech_prefix=_(element_label),
            )
        else:
            element_label = SEMANTIC_ELEMENT_OUTPUT_OPTIONS[element_type][0]
            if forward:
                msg = _("No next {item}")
            else:
                msg = _("No previous {item}")
            speech.announce(msg.format(item=_(element_label)), True)

    def onTextCtrlZoom(self, direction, announce=True):
        self._has_text_zoom = True
        last_pos = self.contentTextCtrl.GetLastPosition()
        existing_style = wx.TextAttr()
        self.contentTextCtrl.GetStyle(0, existing_style)
        new_style = wx.TextAttr(existing_style)
        font = new_style.Font
        size = font.GetPointSize()
        if direction == 1:
            if size > 64:
                return wx.Bell()
            new_style.Font = font.MakeLarger()
            # Translators: a message telling the user that the font size has been increased
            msg = _("The font size has been Increased")
        elif direction == -1:
            if size < 8:
                return wx.Bell()
            new_style.Font = font.MakeSmaller()
            # Translators: a message telling the user that the font size has been decreased
            msg = _("The font size has been decreased")
        else:
            new_style = self.contentTextCtrl.GetDefaultStyle()
            # Translators: a message telling the user that the font size has been reset
            msg = _("The font size has been reset")
            self._has_text_zoom = False
        self.contentTextCtrl.SetStyle(0, last_pos, new_style)
        if announce:
            speech.announce(msg)

    def onSliderValueChanged(self, event):
        target_nav_percentage = event.GetSelection()
        if self.reader.document.is_single_page_document():
            pos_percentage = math.floor(
                self.get_last_position() * (target_nav_percentage / 100)
            )
            target_position = self.get_start_of_line(
                self.get_line_number(pos_percentage)
            )
            self.set_insertion_point(target_position, set_focus_to_text_ctrl=False)
        else:
            page_count = len(self.reader.document)
            target_page = min(
                math.floor(page_count * (target_nav_percentage / 100)), page_count - 1
            )
            self.reader.go_to_page(target_page, set_focus_to_text_ctrl=False)
            target_position = 0
        percentage_display = app.current_language.format_percentage(
            target_nav_percentage / 100
        )
        reading_position_change.send(
            self,
            position=target_position,
            text_to_announce="",
            tts_speech_prefix=_("Reading progress: {percentage}").format(
                percentage=percentage_display
            ),
        )

    def setFrameIcon(self):
        icon_file = app_path(f"{app.name}.ico")
        if icon_file.exists():
            self.SetIcon(wx.Icon(str(icon_file)))

    def set_text_view_margins(self):
        config_margin = round(
            1000 * (config.conf["appearance"]["text_view_margins"] / 100)
        )
        margins = wx.Point(config_margin, config_margin)
        self.contentTextCtrl.SetMargins(margins)

    def get_password_from_user(self):
        password = wx.GetPasswordFromUser(
            # Translators: the content of a dialog asking the user
            # for the password to decrypt the current e-book
            _(
                "This document is encrypted with a password.\n"
                "You need to provide the password in order to access its content.\n"
                "Please provide the password and press enter."
            ),
            # Translators: the title of a dialog asking the user to enter a password to decrypt the e-book
            _("Enter Password"),
            parent=self,
        )
        return password if password else None

    def highlight_range(
        self, start, end, foreground=wx.NullColour, background=wx.NullColour
    ):
        line_start = self.get_containing_line(start)[0]
        attr = wx.TextAttr()
        self.contentTextCtrl.GetStyle(line_start + TEXT_CTRL_OFFSET, attr)
        attr.SetBackgroundColour(wx.YELLOW)
        self.contentTextCtrl.SetStyle(
            start + TEXT_CTRL_OFFSET, end + TEXT_CTRL_OFFSET, attr
        )

    def clear_highlight(self, start=0, end=-1):
        textCtrl = self.contentTextCtrl
        actual_start = start + TEXT_CTRL_OFFSET
        actual_end = end if end < 0 else end + TEXT_CTRL_OFFSET
        if end < 0 or end >= self.get_last_position():
            actual_end = textCtrl.GetLastPosition()
        attr = wx.TextAttr()
        textCtrl.GetStyle(actual_start, attr)
        attr.SetBackgroundColour(textCtrl.BackgroundColour)
        attr.SetTextColour(textCtrl.ForegroundColour)
        textCtrl.SetStyle(actual_start, actual_end, attr)

    def get_statusbar_text(self):
        page = self.reader.get_current_page_object()
        if self.reader.document.is_single_page_document():
            return self.reader.current_book.title
        else:
            page_number = page.number
            if self.reader.document.uses_chapter_by_chapter_navigation_model():
                # Translators: the label of the page content text area
                label_msg = "{chapter}"
            else:
                # Translators: the label of the page content text area
                label_msg = _("Page {page} of {total}")
                label_msg = f"{label_msg} " + chr(0x00B7) + " {chapter}"
                if config.conf["general"]["include_page_label"] and (
                    page_label := page.get_label()
                ):
                    page_number = f"{page_number} ({page_label})"
            return label_msg.format(
                page=page_number,
                total=len(self.reader.document),
                chapter=page.section.title,
            )

    def unselect_text(self):
        self.contentTextCtrl.SelectNone()

    def get_selection_range(self):
        # WHY: Convert real selection range to a clean range.
        start, end = self.contentTextCtrl.GetSelection()
        # If nothing is selected, start can be -1. Handle this gracefully.
        if start == -1:
            return TextRange(self.get_insertion_point(), self.get_insertion_point())
        return TextRange(start - TEXT_CTRL_OFFSET, end - TEXT_CTRL_OFFSET)

    def get_containing_line(self, pos):
        """
        Returns the left and right boundaries
        for the line containing the given position.
        """
        # WHY: A double conversion.
        # 1. Convert clean input position to a real position for the control.
        # 2. Get the real line boundaries from the control.
        # 3. Convert the real boundaries back to clean boundaries for the caller.
        real_pos = pos + TEXT_CTRL_OFFSET
        real_start, real_end = self.contentTextCtrl.GetContainingLine(real_pos)
        return real_start - TEXT_CTRL_OFFSET, real_end - TEXT_CTRL_OFFSET

    def set_text_direction(self, rtl=False):
        style = self.contentTextCtrl.GetDefaultStyle()
        style.SetAlignment(wx.TEXT_ALIGNMENT_RIGHT if rtl else wx.TEXT_ALIGNMENT_LEFT)
        self.contentTextCtrl.SetDefaultStyle(style)

    def notify_user(self, title, message, icon=wx.ICON_INFORMATION, parent=None):
        return wx.MessageBox(message, title, style=icon, parent=parent or self)

    def notify_invalid_action(self):
        wx.Bell()

    def show_html_dialog(self, markup, title):
        browseable_message(markup, title=title, is_html=True)

    def get_line_number(self, pos=None):
        # WHY: Use our own gatekeeper if pos is not provided.
        # Convert the clean position to a real one before querying the control.
        pos = pos or self.get_insertion_point()
        __, __, line_number = self.contentTextCtrl.PositionToXY(pos + TEXT_CTRL_OFFSET)
        return line_number

    def get_start_of_line(self, line_number):
        # WHY: Get the real position from the control, then convert to clean.
        real_pos = self.contentTextCtrl.XYToPosition(0, line_number)
        return max(0, real_pos - TEXT_CTRL_OFFSET)

    def select_text(self, fpos, tpos):
        self.contentTextCtrl.SetFocusFromKbd()
        self.contentTextCtrl.SetSelection(
            fpos + TEXT_CTRL_OFFSET, tpos + TEXT_CTRL_OFFSET
        )

    def set_insertion_point(self, to, set_focus_to_text_ctrl=True):
        actual_position = to + TEXT_CTRL_OFFSET
        self.contentTextCtrl.ShowPosition(actual_position)
        self.contentTextCtrl.SetInsertionPoint(actual_position)
        if set_focus_to_text_ctrl:
            self.contentTextCtrl.SetFocusFromKbd()

    def apply_text_styles(self, style_info):
        default_style = self.contentTextCtrl.GetDefaultStyle()
        available_styles = set(STYLE_TO_WX_TEXT_ATTR_STYLES).intersection(style_info)
        for style_type in available_styles:
            style = wx.TextAttr()
            attr_func, args = STYLE_TO_WX_TEXT_ATTR_STYLES[style_type]
            if callable(args):
                args = (args(default_style),)
            attr_func(style, *args)
            for start, stop in style_info[style_type]:
                self.contentTextCtrl.SetStyle(
                    start + TEXT_CTRL_OFFSET, stop + TEXT_CTRL_OFFSET, style
                )

    def get_insertion_point(self):
        return self.contentTextCtrl.GetInsertionPoint() - TEXT_CTRL_OFFSET

    def get_last_position(self):
        # WHY: The structure is `\n[content]\n`. The real length is `len(content) + 2`.
        # The clean length is `len(content)`. So we must subtract 2.
        # We don't use the offset constant here because we are accounting for
        # the character at the beginning AND the one at the end.
        return self.contentTextCtrl.GetLastPosition() - 2

    def get_text_by_range(self, start, end):
        """Get text by indexes. If end is less than 0 return the text from `start` to the end of the text."""
        actual_start = start + TEXT_CTRL_OFFSET
        actual_end = end if end < 0 else end + TEXT_CTRL_OFFSET
        if end >= self.get_last_position():
            actual_end = self.contentTextCtrl.GetLastPosition() - TEXT_CTRL_OFFSET
        return self.contentTextCtrl.GetRange(actual_start, actual_end)

    def get_text_from_user(
        self, title, label, style=wx.OK | wx.CANCEL | wx.CENTER, value=""
    ):
        dlg = wx.TextEntryDialog(self, label, title, style=style, value=value)
        if dlg.ShowModal() == wx.ID_OK:
            return dlg.GetValue().strip()

    def go_to_webpage(self, url):
        speech.announce(_("Opening page: {url}").format(url=url))
        webbrowser.open_new_tab(url)

    def go_to_position(self, start_pos, end_pos=None):
        if end_pos is None:
            start, end = self.get_containing_line(start_pos)
        else:
            start, end = start_pos, end_pos
        line_text = self.get_text_by_range(start, end)
        self.set_insertion_point(start)
        sounds.navigation.play()
        speech.announce(line_text)

    def is_empty(self):
        return self.get_last_position() <= 0
