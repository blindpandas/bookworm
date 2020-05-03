# coding: utf-8

import time
import wx
from bookworm import config
from bookworm.base_service import BookwormService
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    config_updated,
)


class ContReadingService(BookwormService):
    name = "cont_reading"
    has_gui = False

    def __post_init__(self):
        self.textCtrl = self.view.contentTextCtrl
        self._page_turn_timer = wx.Timer(self.view)
        self._last_page_turn = 0.0
        # Event handling
        self.view.Bind(wx.EVT_TIMER, self.onTimerTick)
        reader_book_unloaded.connect(lambda s:self._page_turn_timer.Stop(), weak=False, sender=self.reader)
        config_updated.connect(self._on_config_changed_for_cont)
        if config.conf["reading"]["use_continuous_reading"]:
            reader_book_loaded.connect(lambda s:self._page_turn_timer.Start(), weak=False, sender=self.reader)

    def shutdown(self):
        self._page_turn_timer.Stop()

    def onTimerTick(self, event):
        cur_pos, end_pos = self.textCtrl.GetInsertionPoint(), self.textCtrl.GetLastPosition()
        if not end_pos:
            return
        if cur_pos == end_pos:
            wx.WakeUpIdle()
            if (time.perf_counter() - self._last_page_turn) < 0.9:
                return
            self.view._nav_provider.navigate_to_page("next")
            self._last_page_turn = time.perf_counter()

    def _on_config_changed_for_cont(self, sender, section):
        if section == "reading":
            is_enabled = config.conf["reading"]["use_continuous_reading"]
            if is_enabled:
                self._page_turn_timer.Start()
            else:
                self._page_turn_timer.Stop()


