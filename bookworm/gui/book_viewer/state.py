# coding: utf-8

import wx
from bookworm.speech.enumerations import SynthState
from bookworm.resources import images
from bookworm.utils import gui_thread_safe
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    app_shuttingdown,
    speech_engine_state_changed,
)
from bookworm.logger import logger
from .menubar import BookRelatedMenuIds


log = logger.getChild(__name__)


class StateProvider:
    """Enables/disables functionality based on current state."""

    def __init__(self):
        reader_book_loaded.connect(self.on_reader_load_unload, sender=self.reader)
        reader_book_unloaded.connect(self.on_reader_load_unload, sender=self.reader)
        speech_engine_state_changed.connect(
            self.on_tts_state_changed, sender=self.reader.tts
        )
        # XXX sent explicitly to disable items upon startup
        reader_book_unloaded.send(self.reader)

    def on_reader_load_unload(self, sender):
        enable = sender.ready
        for item_id in BookRelatedMenuIds:
            item = self.menuBar.FindItemById(item_id.value)
            if not item:
                continue
            item.Enable(enable)
        for ctrl_id in BookRelatedMenuIds:
            ctrl = self.toolbar.FindById(ctrl_id.value)
            if ctrl is not None:
                self.toolbar.EnableTool(ctrl_id.value, enable)
        extra_tools = (wx.ID_PREVIEW_ZOOM_IN, wx.ID_PREVIEW_ZOOM_OUT, self.ppr_id)
        for tool in extra_tools:
            self.toolbar.EnableTool(tool, enable)
        if not enable:
            self.toolbar.SetToolNormalBitmap(self.ppr_id, images.play.GetBitmap())
        # XXX maintain the state upon startup
        speech_engine_state_changed.send(self.reader.tts, state=SynthState.ready)

    @gui_thread_safe
    def on_tts_state_changed(self, sender, state):
        if state is SynthState.busy:
            image = images.pause
        else:
            image = images.play
        self.toolbar.SetToolNormalBitmap(self.ppr_id, image.GetBitmap())
        if not self.reader.ready:
            return
        play = self.menuBar.FindItemById(BookRelatedMenuIds.play)
        pause_toggle = self.menuBar.FindItemById(BookRelatedMenuIds.pauseToggle)
        fastforward = self.menuBar.FindItemById(BookRelatedMenuIds.fastforward)
        rewind = self.menuBar.FindItemById(BookRelatedMenuIds.rewind)
        stop = self.menuBar.FindItemById(BookRelatedMenuIds.stop)
        pause_toggle.Enable(state is not SynthState.ready)
        stop.Enable(state is not SynthState.ready)
        play.Enable(state is not SynthState.busy)
        fastforward.Enable(state is not SynthState.ready)
        rewind.Enable(state is not SynthState.ready)
