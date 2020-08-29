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
        self.view.Bind(wx.EVT_TIMER, self.onTimerTick, self._page_turn_timer)
        reader_book_loaded.connect(self.on_reader_load, weak=False, sender=self.reader)
        reader_book_unloaded.connect(
            lambda s: self._page_turn_timer.Stop(), weak=False, sender=self.reader
        )

    @call_threaded
    def onTimerTick(self, event):
        with self._lock:
            wx.WakeUpIdle()
            end_pos = self.textCtrl.GetLastPosition()
            if not end_pos:
                return
            if self.textCtrl.GetInsertionPoint() == end_pos:
                self.reader.go_to_next()
            self._start_timer()

    def on_reader_load(self, sender):
        if config.conf["reading"]["use_continuous_reading"]:
            self._start_timer()

