# coding: utf-8

import wx
from bookworm.resources import images
from bookworm.utils import gui_thread_safe
from bookworm.signals import reader_book_loaded, reader_book_unloaded, app_shuttingdown
from bookworm.logger import logger
from .menu_constants import BookRelatedMenuIds


log = logger.getChild(__name__)


class StateProvider:
    """Enables/disables functionality based on current state."""

    def __init__(self):
        self.add_load_handler(self.on_reader_load_unload)
        reader_book_unloaded.connect(self.on_reader_load_unload, sender=self.reader)

    def on_reader_load_unload(self, sender):
        enable = sender.ready
        enable_tree = enable and sender.document.has_toc_tree
        self.tocTreeCtrl.Enable(enable_tree)
        focus_ctrl = self.tocTreeCtrl if enable_tree else self.contentTextCtrl
        focus_ctrl.SetFocus()
        stateful_menu_ids = []
        stateful_menu_ids.extend([v.value for v in BookRelatedMenuIds])
        stateful_menu_ids.extend(wx.GetApp().service_handler.get_stateful_menu_ids())
        self.synchronise_menu(stateful_menu_ids, enable)
        extra_tools = (wx.ID_PREVIEW_ZOOM_IN, wx.ID_PREVIEW_ZOOM_OUT)
        for tool in extra_tools:
            self.toolbar.EnableTool(tool, enable)

    def synchronise_menu(self, menu_ids, enable):
        for item_id in menu_ids:
            item = self.menuBar.FindItemById(item_id)
            if not item:
                continue
            item.Enable(enable)
        for ctrl_id in menu_ids:
            ctrl = self.toolbar.FindById(ctrl_id)
            if ctrl is not None:
                self.toolbar.EnableTool(ctrl_id, enable)
