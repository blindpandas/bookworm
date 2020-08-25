# coding: utf-8

import os
import wx
from contextlib import contextmanager
from bookworm import typehints as t
from bookworm import app
from bookworm import config
from bookworm import speech
from bookworm.concurrency import threaded_worker
from bookworm.resources import sounds, images
from bookworm.paths import app_path
from bookworm.reader import (
    EBookReader,
    ReaderError,
    ResourceDoesNotExist,
    UnsupportedDocumentError,
)
from bookworm.signals import reader_book_loaded, reader_book_unloaded
from bookworm.gui.contentview_ctrl import ContentViewCtrl, SelectionRange
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from .menubar import MenubarProvider, BookRelatedMenuIds
from .state import StateProvider
from .navigation import NavigationProvider


log = logger.getChild(__name__)


class ResourceLoader:
    """Loads an ebook into the view."""

    def __init__(self, view, filename, callback=None):
        self.view = view
        self.filename = filename
        self.callback = callback

    def load(self):
        with reader_book_loaded.connected_to(
            self.book_loaded_handler, sender=self.view.reader
        ):
            with self.handle_reader_exceptions():
                self.view.reader.load(self.filename)

    @gui_thread_safe
    def book_loaded_handler(self, sender):
        if sender.document.is_encrypted():
            while True:
                result = self.decrypt_opened_document()
                if result is None:
                    return self.view.unloadCurrentEbook()
                elif result:
                    break
                else:
                    result = self.decrypt_opened_document()
        self.view.invoke_load_handlers()
        if self.callback is not None:
            self.callback()

    @contextmanager
    def handle_reader_exceptions(self):
        has_exception = False
        try:
            yield
        except ResourceDoesNotExist:
            self.view.notify_user(
                # Translators: the title of an error message
                _("File not found"),
                # Translators: the content of an error message
                _("Could not open file: {file}\nThe file does not exist.").format(
                    file=self.filename
                ),
                style=wx.ICON_ERROR,
            )
            log.exception("Failed to open file. File does not exist", exc_info=True)
            has_exception = True
        except UnsupportedDocumentError:
            self.view.notify_user(
                # Translators: the title of a message shown
                # when the format of the e-book is not supported
                _("Unsupported Document Format"),
                # Translators: the content of a message shown
                # when the format of the e-book is not supported
                _("The format of the given document is not supported by Bookworm."),
                icon=wx.ICON_WARNING,
            )
            log.exception("Unsupported file format", exc_info=True)
            has_exception = True
        except ReaderError as e:
            self.view.notify_user(
                # Translators: the title of an error message
                _("Error Openning Document"),
                # Translators: the content of an error message
                _(
                    "Could not open file {file}\n."
                    "Either the file  has been damaged during download, "
                    "or it has been corrupted in some other way."
                ).format(file=self.filename),
                icon=wx.ICON_ERROR,
            )
            log.exception("Error opening document", exc_info=True)
            has_exception = True
        except:
            self.view.notify_user(
                # Translators: the title of an error message
                _("Error Openning Document"),
                # Translators: the content of an error message
                _(
                    "Could not open file {file}\n."
                    "An unknown error occured while loading the file."
                ).format(file=self.filename),
                icon=wx.ICON_ERROR,
            )
            log.exception("Error loading file", exc_info=True)
            has_exception = True
        finally:
            if has_exception:
                self.view.unloadCurrentEbook()
                if app.debug:
                    raise

    def decrypt_opened_document(self):
        reader = self.view.reader
        pwd = wx.GetPasswordFromUser(
            # Translators: the content of a dialog asking the user
            # for the password to decrypt the current e-book
            _(
                "This document is encrypted, and you need a password to access its content.\nPlease enter the password billow and press enter."
            ),
            # Translators: the title of a dialog asking the user to enter a password to decrypt the e-book
            _("Enter Password"),
            parent=self.view,
        )
        if not pwd:
            return
        res = reader.document.decrypt(pwd.GetValue())
        if not res:
            self.view.notify_user(
                # Translators: the title of an error message
                _("Invalid Password"),
                # Translators: the content of a message
                _("The password you've entered is invalid.\nPlease try again."),
                style=wx.ICON_ERROR,
            )
        return bool(res)


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
        )

        # A timer to save the current position to the database
        self.userPositionTimer = wx.Timer(self)

        # Bind Events
        self.Bind(wx.EVT_TIMER, self.onUserPositionTimerTick, self.userPositionTimer)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onTOCItemClick, self.tocTreeCtrl)
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(-1), id=wx.ID_PREVIEW_ZOOM_OUT
        )
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(1), id=wx.ID_PREVIEW_ZOOM_IN
        )

        # Set statusbar text
        # Translators: the text of the status bar when no book is currently open.
        # It is being used also as a label for the page content text area when no book is opened.
        self._no_open_book_status = _("Press (Ctrl + O) to open an ebook")
        self._has_text_zoom = False
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
            | wx.TR_NO_LINES
            | wx.TR_FULL_ROW_HIGHLIGHT
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
        self.add_tools()
        self.toolbar.Realize()
        # Process services menubar
        wx.GetApp().service_handler.process_menubar(self.menuBar)
        self.SetMenuBar(self.menuBar)
        # Set accelerators for the menu items
        self._set_menu_accelerators()
        # XXX sent explicitly to disable items upon startup
        reader_book_unloaded.send(self.reader)

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
            (31, "", "", None),
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

    def open_file(self, filename: t.PathLike, callback=None):
        ResourceLoader(
            self, filename, callback=callback or self.default_book_loaded_callback
        ).load()

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
        self.clear_highlight()
        self.set_title(app.display_name)
        self.set_content("")
        self.set_status(self._no_open_book_status)

    def set_state_on_page_change(self, page):
        self.set_content(page.get_text())
        if config.conf["general"]["play_pagination_sound"]:
            sounds.pagination.play()
        if self.reader.document.is_fluid:
            # Translators: label of content text control when the currently opened
            # document is fluid (does not support paging)
            self.set_status(_("Document content"))
        else:
            # Translators: the label of the page content text area
            cmsg = _("Page {page} of {total} — {chapter}").format(
                page=page.number, total=len(self.reader.document), chapter=page.section.title
            )
            # Translators: a message that is announced after navigating to a page
            smsg = _("Page {page} of {total}").format(
                page=page.number, total=len(self.reader.document)
            )
            self.set_status(cmsg)
            if config.conf["general"]["speak_page_number"]:
                speech.announce(smsg)

    def set_state_on_section_change(self, current):
        self.tocTreeSetSelection(current)
        if config.conf["general"]["speak_section_title"]:
            speech.announce(current.title)

    def onUserPositionTimerTick(self, event):
        try:
            threaded_worker.submit(self.reader.save_current_position)
        except:
            log.exception("Failed to save current position", exc_info=True)

    def onTOCItemClick(self, event):
        selectedItem = event.GetItem()
        self.reader.active_section = self.tocTreeCtrl.GetItemData(selectedItem)
        self.reader.go_to_first_of_section()

    def add_toc_tree(self, tree):
        self.tocTreeCtrl.DeleteAllItems()
        root = self.tocTreeCtrl.AddRoot(tree.title, data=tree)
        self._populate_tree(tree.children, root=root)
        tree.data["tree_id"] = root
        self.tocTreeCtrl.Expand(self.tocTreeCtrl.GetRootItem())

    def tocTreeSetSelection(self, item):
        tree_id = item.data["tree_id"]
        self.tocTreeCtrl.EnsureVisible(tree_id)
        self.tocTreeCtrl.ScrollTo(tree_id)
        self.tocTreeCtrl.SelectItem(tree_id)
        self.tocTreeCtrl.SetFocusedItem(tree_id)

    def clear_toc_tree(self):
        self.tocTreeCtrl.DeleteAllItems()

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

    def _populate_tree(self, toc, root):
        for item in toc:
            entry = self.tocTreeCtrl.AppendItem(root, item.title, data=item)
            item.data["tree_id"] = entry
            if item.children:
                self._populate_tree(item.children, entry)

    def setFrameIcon(self):
        icon_file = app_path(f"{app.name}.ico")
        if icon_file.exists():
            self.SetIcon(wx.Icon(str(icon_file)))

    def _get_text_view_margins(self):
        # XXX need to do some work here to obtain appropriate margins
        return wx.Point(100, 100)

    def highlight_range(
        self, start, end, foreground=wx.NullColour, background=wx.NullColour
    ):
        self.contentTextCtrl.SetStyle(start, end, wx.TextAttr(foreground, background))

    def clear_highlight(self, start=0, end=-1):
        textCtrl = self.contentTextCtrl
        end = textCtrl.LastPosition if end < 0 else end
        textCtrl.SetStyle(
            start,
            end,
            wx.TextAttr(textCtrl.ForegroundColour, textCtrl.BackgroundColour),
        )

    def get_selection_range(self):
        return SelectionRange(*self.contentTextCtrl.GetSelection())

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
        self.contentTextCtrl.SetInsertionPoint(to)

    def get_insertion_point(self):
        return self.contentTextCtrl.GetInsertionPoint()

    def get_text_from_user(
        self, title, label, style=wx.OK | wx.CANCEL | wx.CENTER, value=""
    ):
        dlg = wx.TextEntryDialog(self, label, title, style=style, value=value)
        if dlg.ShowModal() == wx.ID_OK:
            return dlg.GetValue().strip()
