# coding: utf-8

import wx
from bookworm.resources import images
from bookworm import config
from bookworm.logger import logger
from .menubar import BookRelatedMenuIds, ViewerMenuIds


log = logger.getChild(__name__)


class ToolbarProvider:
    """Application toolbar."""

    def __init__(self):
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetWindowStyle(
            wx.TB_FLAT | wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_TEXT
        )
        self.add_tools()

        # Finalize
        self.toolbar.Realize()

        # Events and event handling
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(-1), id=wx.ID_PREVIEW_ZOOM_OUT
        )
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(1), id=wx.ID_PREVIEW_ZOOM_IN
        )

    def add_tools(self):
        tsize = (16, 16)
        self.toolbar.SetToolBitmapSize(tsize)
        tool_info = [
            # Translators: the label of a button in the application toolbar
            (0, "open", _("Open"), wx.ID_OPEN),
            # Translators: the label of a button in the application toolbar
            (10, "search", _("Search"), wx.ID_FIND),
            # Translators: the label of a button in the application toolbar
            (20, "goto", _("Go"), BookRelatedMenuIds.goToPage),
            # Translators: the label of a button in the application toolbar
            (30, "view_image", _("View"), BookRelatedMenuIds.viewRenderedAsImage),
            # Translators: the label of a button in the application toolbar
            (40, "bookmark", _("Bookmark"), BookRelatedMenuIds.addBookmark),
            # Translators: the label of a button in the application toolbar
            (50, "note", _("Note"), BookRelatedMenuIds.addNote),
            # Translators: the label of a button in the application toolbar
            (60, "zoom_out", _("Big"), wx.ID_PREVIEW_ZOOM_OUT),
            # Translators: the label of a button in the application toolbar
            (70, "zoom_in", _("Small"), wx.ID_PREVIEW_ZOOM_IN),
            # Translators: the label of a button in the application toolbar
            (80, "settings", _("Settings"), wx.ID_PREFERENCES),
        ]
        tool_info.extend(wx.GetApp().service_handler.get_toolbar_items())
        tool_info.sort()
        for (pos, imagename, label, ident) in tool_info:
            image = getattr(images, imagename).GetBitmap()
            # Add toolbar item
            self.toolbar.AddTool(
                ident,
                label,
                image,
            )
