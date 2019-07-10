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
        self.ppr_id = wx.NewIdRef()

        tsize = (24, 24)
        open_bmp = images.open.GetBitmap()
        bookmark_bmp = images.bookmark.GetBitmap()
        search_bmp = images.search.GetBitmap()
        goto_bmp = images.goto.GetBitmap()
        view_image_bmp = images.view_image.GetBitmap()
        self.toolbar.SetToolBitmapSize(tsize)

        # Add toolbar items
        self.toolbar.AddTool(wx.ID_OPEN, "Open", open_bmp, "Open an e-book")
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_FIND, "Search", search_bmp, "Search e-book")
        self.toolbar.AddTool(BookRelatedMenuIds.goToPage, "Go", goto_bmp, "Go to page")
        self.toolbar.AddTool(
            BookRelatedMenuIds.viewRenderedAsImage,
            "View",
            view_image_bmp,
            "View a fully rendered version of this page",
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(
            BookRelatedMenuIds.addBookmark, "Bookmark", bookmark_bmp, "Add bookmark"
        )
        self.toolbar.AddTool(
            BookRelatedMenuIds.addNote, "Note", images.note.GetBitmap(), "Add note"
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(
            BookRelatedMenuIds.rewind,
            "Rewind",
            images.rewind.GetBitmap(),
            "Skip to previous paragraph",
        )
        self.toolbar.AddTool(
            self.ppr_id, "Play", images.play.GetBitmap(), "Play/Resume"
        )
        self.toolbar.AddTool(
            BookRelatedMenuIds.fastforward,
            "Fast Forward",
            images.fastforward.GetBitmap(),
            "Skip to next paragraph",
        )
        self.toolbar.AddTool(
            ViewerMenuIds.voiceProfiles,
            "Voice",
            images.profile.GetBitmap(),
            "Customize TTS voice parameters.",
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(
            wx.ID_PREVIEW_ZOOM_OUT,
            "Zoom out",
            images.zoom_out.GetBitmap(),
            "Make font smaller",
        )
        self.toolbar.AddTool(
            wx.ID_PREVIEW_ZOOM_IN,
            "Zoom in",
            images.zoom_in.GetBitmap(),
            "Make font larger",
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(
            wx.ID_PREFERENCES,
            "Preferences",
            images.settings.GetBitmap(),
            "Configure application",
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
