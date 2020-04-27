# coding: utf-8

import wx
from bookworm.resources import images
from bookworm import config
from bookworm.speech.enumerations import SynthState
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

        tsize = (24, 24)
        open_bmp = images.open.GetBitmap()
        bookmark_bmp = images.bookmark.GetBitmap()
        search_bmp = images.search.GetBitmap()
        goto_bmp = images.goto.GetBitmap()
        view_image_bmp = images.view_image.GetBitmap()
        self.toolbar.SetToolBitmapSize(tsize)

        # Add toolbar items
        self.toolbar.AddTool(
            wx.ID_OPEN,
            # Translators: the label of a button in the application toolbar
            _("Open"),
            open_bmp,
            # Translators: the help text of a button in the application toolbar
            _("Open an e-book"),
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(
            wx.ID_FIND,
            # Translators: the label of a button in the application toolbar
            _("Search"),
            search_bmp,
            # Translators: the help text of a button in the application toolbar
            _("Search e-book"),
        )
        self.toolbar.AddTool(
            BookRelatedMenuIds.goToPage,
            # Translators: the label of a button in the application toolbar
            _("Go"),
            goto_bmp,
            # Translators: the help text of a button in the application toolbar
            _("Go to page"),
        )
        self.toolbar.AddTool(
            BookRelatedMenuIds.viewRenderedAsImage,
            # Translators: the label of a button in the application toolbar
            _("View"),
            view_image_bmp,
            # Translators: the help text of a button in the application toolbar
            _("View a fully rendered version of this page"),
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(
            BookRelatedMenuIds.addBookmark,
            # Translators: the label of a button in the application toolbar
            _("Bookmark"),
            bookmark_bmp,
            # Translators: the help text of a button in the application toolbar
            _("Add bookmark"),
        )
        self.toolbar.AddTool(
            BookRelatedMenuIds.addNote,
            # Translators: the label of a button in the application toolbar
            _("Note"),
            images.note.GetBitmap(),
            # Translators: the help text of a button in the application toolbar
            _("Add note"),
        )
        self.toolbar.AddTool(
            wx.ID_PREVIEW_ZOOM_OUT,
            # Translators: the label of a button in the application toolbar
            _("Zoom out"),
            images.zoom_out.GetBitmap(),
            # Translators: the help text of a button in the application toolbar
            _("Make font smaller"),
        )
        self.toolbar.AddTool(
            wx.ID_PREVIEW_ZOOM_IN,
            # Translators: the label of a button in the application toolbar
            _("Zoom in"),
            images.zoom_in.GetBitmap(),
            # Translators: the help text of a button in the application toolbar
            _("Make font larger"),
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(
            wx.ID_PREFERENCES,
            # Translators: the label of a button in the application toolbar
            _("Preferences"),
            images.settings.GetBitmap(),
            # Translators: the help text of a button in the application toolbar
            _("Configure the application"),
        )

        # Finalize
        self.toolbar.Realize()

        # Events and event handling
        self.Bind(wx.EVT_TOOL, self.onPPR, id=self.ppr_id)
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(-1), id=wx.ID_PREVIEW_ZOOM_OUT
        )
        self.Bind(
            wx.EVT_TOOL, lambda e: self.onTextCtrlZoom(1), id=wx.ID_PREVIEW_ZOOM_IN
        )

    def onPPR(self, event):
        if (not self.reader.tts.is_ready) or (
            self.reader.tts.engine.state is SynthState.ready
        ):
            self.onPlay(event)
        else:
            self.onPauseToggle(event)
