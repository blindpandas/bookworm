# coding: utf-8

import wx
from math import ceil
from contextlib import contextmanager
from concurrent.futures import Future
from functools import partial
from pathlib import Path
from bookworm import typehints as t
from bookworm import app
from bookworm import config
from bookworm import speech
from bookworm.concurrency import threaded_worker, CancellationToken
from bookworm.resources import sounds, images
from bookworm.paths import app_path
from bookworm.structured_text import Style, SEMANTIC_ELEMENT_OUTPUT_OPTIONS
from bookworm.reader import (
    EBookReader,
    UriResolver,
    ReaderError,
    ResourceDoesNotExist,
    UnsupportedDocumentError,
)
from bookworm.signals import reader_book_loaded, reader_book_unloaded
from bookworm.structured_text import TextRange
from bookworm.gui.contentview_ctrl import ContentViewCtrl
from bookworm.gui.components import TocTreeManager, AsyncSnakDialog
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from .menubar import MenubarProvider, BookRelatedMenuIds
from .state import StateProvider
from .navigation import NavigationProvider


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
            doc = self.resolve_document(resolver)
            if doc is not None:
                self.load(doc)
        else:
            AsyncSnakDialog(
                task=partial(self.resolve_document, resolver),
                done_callback=self.load,
                dismiss_callback=lambda: self._cancellation_token.request_cancellation()
                or True,
                message=_("Opening document, please wait..."),
            )

    def resolve_document(self, resolver):
        _last_exception = None
        try:
            return resolver.read_document()
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
        except ReaderError as e:
            _last_exception = e
            log.exception("Unsupported file format", exc_info=True)
            wx.CallAfter(
                self.view.notify_user,
                # Translators: the title of an error message
                _("Error Openning Document"),
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
            log.exception("Unsupported file format", exc_info=True)
            wx.CallAfter(
                self.view.notify_user,
                # Translators: the title of an error message
                _("Error Openning Document"),
                # Translators: the content of an error message
                _(
                    "Could not open document\n."
                    "An unknown error occured while loading the file."
                ),
                icon=wx.ICON_ERROR,
            )
        finally:
            if _last_exception is not None:
                wx.CallAfter(self.view.unloadCurrentEbook)
                if app.debug:
                    raise _last_exception

    def load(self, document):
        with reader_book_loaded.connected_to(
            self.book_loaded_handler, sender=self.view.reader
        ):
            if isinstance(document, Future):
                document = document.result()
            if (document is not None) and (
                not self._cancellation_token.is_cancellation_requested()
            ):
                self.view.reader.set_document(document)

    @gui_thread_safe
    def book_loaded_handler(self, sender):
        self.view.invoke_load_handlers()
        if self.callback is not None:
            self.callback()


class BookViewerWindow(wx.Frame, MenubarProvider, StateProvider):
    """The book viewer window."""

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, name="main_window")
        self.setFrameIcon()

        self.reader = EBookReader(self)
        self._book_loaded_handlers = []
        self.createControls()

        self.toolbar = self.CreateToolBar()
        self.toolbar.SetWindowStyle(
            wx.TB_FLAT | wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_TEXT
        )
        self.CreateStatusBar()
        self._nav_provider = NavigationProvider(
            ctrl=self.contentTextCtrl,
            reader=self.reader,
            zoom_callback=self.onTextCtrlZoom,
            view=self,
        )

        # A timer to save the current position to the database
        self.userPositionTimer = wx.Timer(self)

        # Bind Events
        self.Bind(wx.EVT_TIMER, self.onUserPositionTimerTick, self.userPositionTimer)
        self.tocTreeCtrl.Bind(wx.EVT_SET_FOCUS, self.onTocTreeFocus, self.tocTreeCtrl)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onTOCItemClick, self.tocTreeCtrl)
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(-1), id=wx.ID_PREVIEW_ZOOM_OUT
        )
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(1), id=wx.ID_PREVIEW_ZOOM_IN
        )

        self.toc_tree_manager = TocTreeManager(self.tocTreeCtrl)
        # Set statusbar text
        # Translators: the text of the status bar when no book is currently open.
        # It is being used also as a label for the page content text area when no book is opened.
        self._no_open_book_status = _("Press (Ctrl + O) to open a document")
        self._has_text_zoom = False
        self.__latest_structured_navigation_position = None
        self.set_status(self._no_open_book_status)
        StateProvider.__init__(self)
        MenubarProvider.__init__(self)

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
            style=wx.TR_TWIST_BUTTONS
            | wx.TR_LINES_AT_ROOT
            | wx.TR_FULL_ROW_HIGHLIGHT
            | wx.TR_SINGLE
            | wx.TR_ROW_LINES,
            name="toc_tree",
        )
        # Translators: the label of the text area which shows the
        # content of the current page
        self.contentTextCtrlLabel = wx.StaticText(panel, -1, _("Content"))
        self.contentTextCtrl = ContentViewCtrl(
            panel,
            size=(200, 160),
            name="content_view",
        )
        self.contentTextCtrl.SetMargins(self._get_text_view_margins())

        # Use a sizer to layout the controls, stacked horizontally and with
        # a 10 pixel border around each
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        lftSizer = wx.BoxSizer(wx.VERTICAL)
        rgtSizer = wx.BoxSizer(wx.VERTICAL)
        lftSizer.Add(tocTreeLabel, 0, wx.ALL, 5)
        lftSizer.Add(self.tocTreeCtrl, 1, wx.ALL, 5)
        rgtSizer.Add(self.contentTextCtrlLabel, 0, wx.EXPAND | wx.ALL, 5)
        rgtSizer.Add(self.contentTextCtrl, 1, wx.EXPAND | wx.ALL, 5)
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
        self.SetMinSize(self.GetSize())
        self.CenterOnScreen(wx.BOTH)

    def finalize_gui_creation(self):
        self.set_content_view_font()
        self.add_tools()
        self.toolbar.Realize()
        # Process services menubar
        wx.GetApp().service_handler.process_menubar(self.menuBar)
        self.SetMenuBar(self.menuBar)
        # Set accelerators for the menu items
        self._set_menu_accelerators()
        # XXX sent explicitly to disable items upon startup
        reader_book_unloaded.send(self.reader)

    def set_content_view_font(self):
        finfo = wx.FontInfo().FaceName(config.conf["appearance"]["font_facename"])
        configured_font = wx.Font(finfo)
        configured_font.SetPointSize(config.conf["appearance"]["font_point_size"])
        default_style = wx.TextAttr()
        default_style.SetFont(configured_font)
        self.contentTextCtrl.SetDefaultStyle(default_style)

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
            (20, "goto", _("Go"), BookRelatedMenuIds.goToPage),
            # Translators: the label of a button in the application toolbar
            (30, "view_image", _("View"), BookRelatedMenuIds.viewRenderedAsImage),
            (31, "reading_mode", _("Mode"), BookRelatedMenuIds.changeReadingMode),
            (32, "", "", None),
            # Translators: the label of a button in the application toolbar
            (60, "zoom_out", _("Big"), wx.ID_PREVIEW_ZOOM_OUT),
            # Translators: the label of a button in the application toolbar
            (70, "zoom_in", _("Small"), wx.ID_PREVIEW_ZOOM_IN),
            (71, "", "", None),
            # Translators: the label of a button in the application toolbar
            (80, "settings", _("Settings"), wx.ID_PREFERENCES),
        ]
        tool_info.extend(wx.GetApp().service_handler.get_toolbar_items())
        tool_info.sort()
        for (pos, imagename, label, ident) in tool_info:
            if ident is None:
                self.toolbar.AddSeparator()
                continue
            image = getattr(images, imagename).GetBitmap()
            # Add toolbar item
            self.toolbar.AddTool(ident, label, image)

    def add_load_handler(self, func):
        self._book_loaded_handlers.append(func)

    def invoke_load_handlers(self):
        for func in self._book_loaded_handlers:
            func(self.reader)

    def default_book_loaded_callback(self):
        self.userPositionTimer.Start(1500)
        if self.contentTextCtrl.HasFocus():
            self.tocTreeCtrl.SetFocus()

    def open_uri(self, uri, callback=None):
        self.unloadCurrentEbook()
        ResourceLoader(
            self, uri, callback=callback or self.default_book_loaded_callback
        )

    def open_document(self, document):
        self.unloadCurrentEbook()
        self.view.reader.set_document(document)

    def set_content(self, content):
        self.contentTextCtrl.Clear()
        self.contentTextCtrl.WriteText(content)
        self.contentTextCtrl.SetInsertionPoint(0)
        if self._has_text_zoom:
            self.contentTextCtrl.SetFont(self.contentTextCtrl.Font.MakeSmaller())
            self.contentTextCtrl.SetFont(self.contentTextCtrl.Font.MakeLarger())

    def set_title(self, title):
        self.SetTitle(title)

    def set_status(self, text, statusbar_only=False, *args, **kwargs):
        super().SetStatusText(text, *args, **kwargs)
        if not statusbar_only:
            self.contentTextCtrlLabel.SetLabel(text)

    def unloadCurrentEbook(self):
        self.userPositionTimer.Stop()
        self.reader.unload()
        self.clear_toc_tree()
        self.set_title(app.display_name)
        self.set_content("")
        self.clear_highlight()
        self.set_status(self._no_open_book_status)

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
        if not is_single_page_doc and config.conf["general"]["speak_section_title"]:
            speech.announce(current.title)

    def onUserPositionTimerTick(self, event):
        try:
            threaded_worker.submit(self.reader.save_current_position)
        except:
            log.exception("Failed to save current position", exc_info=True)

    def onTocTreeFocus(self, event):
        event.Skip(True)
        if not self.reader.document.is_single_page_document():
            return
        condition = (
            self.reader.ready
            and self.get_insertion_point() not in self.reader.active_section.text_range
        )
        if condition:
            with self.mute_page_and_section_speech():
                self.reader.active_section = (
                    self.reader.document.get_section_at_position(
                        self.get_insertion_point()
                    )
                )
                event.GetEventObject().SetFocus()

    def onTOCItemClick(self, event):
        with self.mute_page_and_section_speech():
            selectedItem = event.GetItem()
            self.reader.active_section = self.tocTreeCtrl.GetItemData(selectedItem)
            self.reader.go_to_first_of_section()
            self.contentTextCtrl.SetFocus()

    def set_state_on_page_change(self, page):
        self.set_content(page.get_text())
        if config.conf["general"]["play_pagination_sound"]:
            sounds.pagination.play()
        if self.reader.document.is_single_page_document():
            # Translators: label of content text control when the currently opened
            # document is a single page document
            self.set_status(_("Document content"))
        else:
            page_number = page.number
            if self.reader.document.uses_chapter_by_chapter_navigation_model():
                # Translators: the label of the page content text area
                label_msg = _("{chapter}")
            else:
                # Translators: the label of the page content text area
                label_msg = _("Page {page} of {total} — {chapter}")
                if config.conf["general"]["include_page_label"] and (
                    page_label := page.get_label()
                ):
                    page_number = f"{page_number} ({page_label})"
            self.set_status(
                label_msg.format(
                    page=page_number,
                    total=len(self.reader.document),
                    chapter=page.section.title,
                )
            )
            if config.conf["general"]["speak_page_number"]:
                # Translators: a message that is announced after navigating to a page
                spoken_msg = _("Page {page} of {total}").format(
                    page=page.number, total=len(self.reader.document)
                )
                speech.announce(spoken_msg)

    @contextmanager
    def mute_page_and_section_speech(self):
        opsc = config.conf["general"]["speak_page_number"]
        ossc = config.conf["general"]["speak_section_title"]
        config.conf["general"]["speak_page_number"] = False
        config.conf["general"]["speak_section_title"] = False
        try:
            yield
        finally:
            config.conf["general"]["speak_page_number"] = opsc
            config.conf["general"]["speak_section_title"] = ossc

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
            element_label, should_speak_whole_text = SEMANTIC_ELEMENT_OUTPUT_OPTIONS[
                actual_element_type
            ]
            line_start, line_stop = self.get_containing_line(start + 1)
            tstart, tstop = (
                (start, stop) if should_speak_whole_text else (line_start, line_stop)
            )
            text = self.contentTextCtrl.GetRange(tstart, tstop)
            msg = _("{text}: {item_type}").format(text=text, item_type=_(element_label))
            target_position = self.get_containing_line(tstop - 1)[0]
            self.set_insertion_point(target_position)
            sounds.structured_navigation.play()
            speech.announce(msg)
        else:
            element_label = SEMANTIC_ELEMENT_OUTPUT_OPTIONS[element_type][0]
            if forward:
                msg = _("No next {item}")
            else:
                msg = _("No previous {item}")
            speech.announce(msg.format(item=element_label))

    def onTextCtrlZoom(self, direction):
        self._has_text_zoom = True
        font = self.contentTextCtrl.GetFont()
        size = font.GetPointSize()
        if direction == 1:
            if size >= 64:
                return wx.Bell()
            self.contentTextCtrl.SetFont(font.MakeLarger())
            # Translators: a message telling the user that the font size has been increased
            msg = _("The font size has been Increased")
        elif direction == -1:
            if size <= 6:
                return wx.Bell()
            self.contentTextCtrl.SetFont(font.MakeSmaller())
            # Translators: a message telling the user that the font size has been decreased
            msg = _("The font size has been decreased")
        else:
            self.contentTextCtrl.SetFont(wx.NullFont)
            # Translators: a message telling the user that the font size has been reset
            msg = _("The font size has been reset")
            self._has_text_zoom = False
        speech.announce(msg)

    def setFrameIcon(self):
        icon_file = app_path(f"{app.name}.ico")
        if icon_file.exists():
            self.SetIcon(wx.Icon(str(icon_file)))

    def _get_text_view_margins(self):
        # XXX need to do some work here to obtain appropriate margins
        return wx.Point(75, 75)

    def try_decrypt_document(self, document):
        if not document.is_encrypted():
            return True
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
        if not password:
            return False
        result = document.decrypt(password)
        if not result:
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
            return self.try_decrypt_document(document)
        return result

    def highlight_range(
        self, start, end, foreground=wx.NullColour, background=wx.NullColour
    ):
        line_start = self.get_containing_line(start)[0]
        attr = wx.TextAttr()
        self.contentTextCtrl.GetStyle(line_start, attr)
        attr.SetBackgroundColour(wx.YELLOW)
        self.contentTextCtrl.SetStyle(start, end, attr)

    def clear_highlight(self, start=0, end=-1):
        textCtrl = self.contentTextCtrl
        end = end if end >= 0 else textCtrl.LastPosition
        attr = wx.TextAttr()
        textCtrl.GetStyle(self.get_containing_line(start)[0], attr)
        attr.SetBackgroundColour(textCtrl.BackgroundColour)
        attr.SetTextColour(textCtrl.ForegroundColour)
        textCtrl.SetStyle(
            start,
            end,
            attr,
        )

    def get_selection_range(self):
        return TextRange(*self.contentTextCtrl.GetSelection())

    def get_containing_line(self, pos):
        """
        Returns the left and right boundaries
        for the line containing the given position.
        """
        return self.contentTextCtrl.GetContainingLine(pos)

    def set_text_direction(self, rtl=False):
        style = self.contentTextCtrl.GetDefaultStyle()
        style.SetAlignment(wx.TEXT_ALIGNMENT_RIGHT if rtl else wx.TEXT_ALIGNMENT_LEFT)
        self.contentTextCtrl.SetDefaultStyle(style)

    def notify_user(self, title, message, icon=wx.ICON_INFORMATION, parent=None):
        return wx.MessageBox(message, title, style=icon, parent=parent or self)

    def get_line_number(self, pos=None):
        pos = pos or self.contentTextCtrl.InsertionPoint
        __, __, line_number = self.contentTextCtrl.PositionToXY(pos)
        return line_number

    def select_text(self, fpos, tpos):
        self.contentTextCtrl.SetFocusFromKbd()
        self.contentTextCtrl.SetSelection(fpos, tpos)

    def set_insertion_point(self, to):
        self.contentTextCtrl.SetFocusFromKbd()
        self.contentTextCtrl.ShowPosition(to)
        self.contentTextCtrl.SetInsertionPoint(to)

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
                self.contentTextCtrl.SetStyle(start, stop, style)

    def get_insertion_point(self):
        return self.contentTextCtrl.GetInsertionPoint()

    def get_text_from_user(
        self, title, label, style=wx.OK | wx.CANCEL | wx.CENTER, value=""
    ):
        dlg = wx.TextEntryDialog(self, label, title, style=style, value=value)
        if dlg.ShowModal() == wx.ID_OK:
            return dlg.GetValue().strip()
