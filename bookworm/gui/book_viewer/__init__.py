# coding: utf-8

import os
import wx
from bookworm import app
from bookworm import config
from bookworm import speech
from bookworm.resources import images
from bookworm.paths import app_path
from bookworm.reader import EBookReader
from bookworm.signals import reader_book_unloaded, reader_page_changed
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from .decorators import only_when_reader_ready
from .menubar import MenubarProvider, BookRelatedMenuIds
from .state import StateProvider
from .navigation import NavigationProvider


log = logger.getChild(__name__)


class BookViewerWindow(wx.Frame, MenubarProvider, StateProvider):
    """The book viewer window."""

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, name="main_window")
        self.setFrameIcon()

        self.reader = EBookReader(self)
        MenubarProvider.__init__(self)

        self.toolbar = self.CreateToolBar()
        self.toolbar.SetWindowStyle(
            wx.TB_FLAT | wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_TEXT
        )
        self.CreateStatusBar()

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
        self.contentTextCtrl = wx.TextCtrl(
            panel,
            size=(200, 160),
            style=wx.TE_READONLY
            | wx.TE_MULTILINE
            | wx.TE_RICH2
            | wx.TE_AUTO_URL
            | wx.TE_PROCESS_ENTER
            | wx.TE_NOHIDESEL,
            name="content_view",
        )
        self.contentTextCtrl.Bind(
            wx.EVT_CONTEXT_MENU, lambda e: e.Skip(False), self.contentTextCtrl
        )
        self.contentTextCtrl.Bind(
            wx.EVT_RIGHT_UP, self.onContentTextCtrlContextMenu, self.contentTextCtrl
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

        # Bind Events
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
        self.SetStatusText(self._no_open_book_status)
        StateProvider.__init__(self)
        self._nav_provider = NavigationProvider(
            ctrl=self.contentTextCtrl,
            reader=self.reader,
            zoom_callback=self.onTextCtrlZoom,
        )

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

    def set_content(self, content):
        self.contentTextCtrl.Clear()
        self.contentTextCtrl.WriteText(content)
        self.contentTextCtrl.SetInsertionPoint(0)
        if self._has_text_zoom:
            self.contentTextCtrl.SetFont(self.contentTextCtrl.Font.MakeSmaller())
            self.contentTextCtrl.SetFont(self.contentTextCtrl.Font.MakeLarger())

    def SetStatusText(self, text, statusbar_only=False, *args, **kwargs):
        super().SetStatusText(text, *args, **kwargs)
        if not statusbar_only:
            self.contentTextCtrlLabel.SetLabel(text)

    @only_when_reader_ready
    def unloadCurrentEbook(self):
        self.reader.unload()
        self.set_content("")
        self.SetStatusText(self._no_open_book_status)
        self.tocTreeCtrl.DeleteAllItems()
        self.Title = app.display_name
        self._reset_search_history()
        self.populate_recent_file_list()

    @only_when_reader_ready
    def onTOCItemClick(self, event):
        selectedItem = event.GetItem()
        self.reader.active_section = self.tocTreeCtrl.GetItemData(selectedItem)
        self.reader.go_to_first_of_section()

    def add_toc_tree(self, tree):
        self.tocTreeCtrl.DeleteAllItems()
        root = self.tocTreeCtrl.AddRoot(tree.title, data=tree)
        self._populate_tree(tree.children, root=root)
        tree.data["tree_id"] = root

    def tocTreeSetSelection(self, item):
        tree_id = item.data["tree_id"]
        self.tocTreeCtrl.EnsureVisible(tree_id)
        self.tocTreeCtrl.ScrollTo(tree_id)
        self.tocTreeCtrl.SelectItem(tree_id)
        self.tocTreeCtrl.SetFocusedItem(tree_id)

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

    @gui_thread_safe
    def highlight_range(self, start, end, foreground=None, background=None):
        foreground = foreground or wx.NullColour
        background = background or wx.NullColour
        self.contentTextCtrl.SetStyle(start, end, wx.TextAttr(foreground, background))

    @gui_thread_safe
    def clear_highlight(self, start=0, end=-1):
        textCtrl = self.contentTextCtrl
        end = textCtrl.LastPosition if end < 0 else end
        textCtrl.SetStyle(
            start,
            end,
            wx.TextAttr(textCtrl.ForegroundColour, textCtrl.BackgroundColour),
        )

    def get_containing_line(self, pos):
        """Returns the left and right boundaries
        for the line containing the given position.
        """
        _, col, lino = self.contentTextCtrl.PositionToXY(pos)
        left = pos - col
        return (left, left + self.contentTextCtrl.GetLineLength(lino))

    def set_text_direction(self, rtl=False):
        style = self.contentTextCtrl.GetDefaultStyle()
        style.SetAlignment(wx.TEXT_ALIGNMENT_RIGHT if rtl else wx.TEXT_ALIGNMENT_LEFT)
        self.contentTextCtrl.SetDefaultStyle(style)

    def notify_user(self, title, message, icon=wx.ICON_INFORMATION):
        wx.MessageBox(message, title, style=icon)

    def get_line_number(self, pos=None):
        pos = pos or self.contentTextCtrl.InsertionPoint
        __, __, line_number = self.contentTextCtrl.PositionToXY(pos)
        return line_number
