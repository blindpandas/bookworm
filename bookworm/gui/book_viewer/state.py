# coding: utf-8

import wx
from bookworm.resources import images
from bookworm.utils import gui_thread_safe
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    app_shuttingdown,
)
from bookworm.logger import logger
from .menubar import BookRelatedMenuIds


log = logger.getChild(__name__)


class StateProvider:
    """Enables/disables functionality based on current state."""

    def __init__(self):
        reader_book_loaded.connect(self.on_reader_load_unload, sender=self.reader)
        reader_book_unloaded.connect(self.on_reader_load_unload, sender=self.reader)
        # XXX sent explicitly to disable items upon startup
        reader_book_unloaded.send(self.reader)

    def on_reader_load_unload(self, sender):
        enable = sender.ready
        self.tocTreeCtrl.Enable(enable)
        focus_ctrl = self.tocTreeCtrl if enable else self.contentTextCtrl
        focus_ctrl.SetFocus()
        for item_id in BookRelatedMenuIds:
            item = self.menuBar.FindItemById(item_id.value)
            if not item:
                continue
            item.Enable(enable)
        for ctrl_id in BookRelatedMenuIds:
            ctrl = self.toolbar.FindById(ctrl_id.value)
            if ctrl is not None:
                self.toolbar.EnableTool(ctrl_id.value, enable)
        extra_tools = (wx.ID_PREVIEW_ZOOM_IN, wx.ID_PREVIEW_ZOOM_OUT)
        for tool in extra_tools:
            self.toolbar.EnableTool(tool, enable)

