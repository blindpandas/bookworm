# coding: utf-8

import time
import threading
import wx
from bookworm import config
from bookworm.base_service import BookwormService
from bookworm.concurrency import call_threaded
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    config_updated,
)


# Timer Interval
TIMER_INTERVAL = 50


class ContReadingService(BookwormService):
    name = "cont_reading"
    has_gui = False

    def __post_init__(self):
        self.textCtrl = self.view.contentTextCtrl
        self._page_turn_timer = wx.Timer(self.view)
        self._start_timer = lambda: self._page_turn_timer.Start(
            TIMER_INTERVAL, wx.TIMER_ONE_SHOT
        )
        self._lock = threading.Lock()
        # Event handling
        self.view.Bind(wx.EVT_TIMER, self.onTimerTick)
        reader_book_unloaded.connect(
            lambda s: self._page_turn_timer.Stop(), weak=False, sender=self.reader
        )
        config_updated.connect(self._on_config_changed_for_cont)
        if config.conf["reading"]["use_continuous_reading"]:
            reader_book_loaded.connect(
                lambda s: self._start_timer(), weak=False, sender=self.reader
            )

    @call_threaded
    def onTimerTick(self, event):
        with self._lock:
            wx.WakeUpIdle()
            cur_pos, end_pos = (
                self.textCtrl.GetInsertionPoint(),
                self.textCtrl.GetLastPosition(),
            )
            if not end_pos:
                return
            if cur_pos == end_pos:
                self.reader.go_to_next()
            self._start_timer()

    def _on_config_changed_for_cont(self, sender, section):
        if section == "reading":
            is_enabled = config.conf["reading"]["use_continuous_reading"]
            if is_enabled:
                self._page_turn_timer.Start()
            else:
                self._page_turn_timer.Stop()
