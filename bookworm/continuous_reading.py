# coding: utf-8

import threading
import time
import winsound

import wx

from bookworm import config
from bookworm.concurrency import call_threaded
from bookworm.service import BookwormService
from bookworm.signals import (config_updated, reader_book_loaded,
                              reader_book_unloaded, reader_page_changed)


class ContReadingService(BookwormService):
    name = "cont_reading"
    has_gui = False

    def __post_init__(self):
        self._book_opened = threading.Event()
        self._page_turn_barrier = threading.Barrier(2)
        # Event handling
        reader_book_loaded.connect(self.on_reader_load, weak=False, sender=self.reader)
        reader_book_unloaded.connect(
            lambda s: self._book_opened.clear(), weak=False, sender=self.reader
        )
        self._worker_thread = threading.Thread(
            target=self.start_monitoring,
            args=(self.view.contentTextCtrl, self.reader),
            daemon=True,
            name="bookworm.continuous.reading.service",
        )
        self._worker_thread.start()

    def start_monitoring(self, textCtrl, reader):
        while True:
            if not reader.ready:
                self._book_opened.wait()
            # The wx Control may be already destroied
            if not textCtrl:
                return
            wx.CallAfter(wx.WakeUpIdle)
            if wx.GetKeyState(wx.WXK_CONTROL):
                continue
            end_pos = textCtrl.GetLastPosition()
            if not end_pos:
                continue
            if textCtrl.GetInsertionPoint() == end_pos:
                wx.CallAfter(textCtrl.SetInsertionPoint, 0)
                wx.CallAfter(reader.go_to_next)
                time.sleep(3.0)
            else:
                time.sleep(0.1)

    def on_reader_load(self, sender):
        if (
            config.conf["reading"]["use_continuous_reading"]
            and not sender.document.is_single_page_document()
        ):
            self._book_opened.set()
