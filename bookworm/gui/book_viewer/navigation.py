# coding: utf-8

import time
import wx
from bookworm import config
from bookworm.signals import reader_page_changed
from bookworm.logger import logger
from .decorators import only_when_reader_ready


# Time_out of consecutive key presses in seconds
DKEY_TIMEOUT = 0.75

class NavigationProvider:
    """Implements keyboard navigation for viewer controls."""

    def __init__(self, ctrl, reader, callback_func=None, zoom_callback=None):
        self.textCtrl = ctrl
        self.reader = reader
        self.callback_func = callback_func
        self.zoom_callback = zoom_callback
        self._key_press_record = {}
        if self.zoom_callback:
            self.zoom_keymap = {ord("0"): 0, ord("="): 1, ord("-"): -1}
        ctrl.Bind(wx.EVT_KEY_UP, self.onKeyUp, ctrl)
        reader_page_changed.connect(self._reset_up_arrow_pressed_time, weak=False)
        # Funky  thinks can happen if we use normal `Key up` event to capture enter in wx.TextCtrl
        if isinstance(ctrl, wx.TextCtrl):
            ctrl.Bind(wx.EVT_TEXT_ENTER, self._text_ctrl_navigate_next, ctrl)

    def callback(self):
        if self.callback_func is not None:
            return self.callback_func()

    @only_when_reader_ready
    def onKeyUp(self, event):
        event.Skip()
        key_code = event.GetKeyCode()
        if isinstance(event.GetEventObject(), wx.TextCtrl) and key_code in (wx.WXK_UP, wx.WXK_DOWN):
            if config.conf["reading"]["use_continuous_reading"]:
                self._auto_navigate(key_code)
        elif key_code in (wx.WXK_RETURN, wx.WXK_BACK):
            if (
                not isinstance(event.GetEventObject(), wx.TextCtrl)
                and key_code == wx.WXK_RETURN
            ):
                self.navigate_to_page(to="next")
            elif key_code == wx.WXK_BACK:
                self.navigate_to_page(to="prev")
            self.callback()
        elif isinstance(event.GetEventObject(), wx.TextCtrl) and key_code == wx.WXK_PAGEDOWN:
            self.textCtrl.InsertionPoint = self.textCtrl.GetLastPosition() - 1
            event.Skip(False)
        if event.GetModifiers() == wx.MOD_ALT and key_code in (
            wx.WXK_PAGEUP,
            wx.WXK_PAGEDOWN,
        ):
            if key_code == wx.WXK_PAGEDOWN:
                self.reader.navigate(to="next", unit="section")
            elif key_code == wx.WXK_PAGEUP:
                self.reader.navigate(to="prev", unit="section")
            self.callback()
        if event.GetModifiers() == wx.MOD_ALT and key_code in (
            wx.WXK_RIGHT,
            wx.WXK_LEFT,
        ):
            if not self.reader.tts.is_ready:
                return wx.Bell()
            if key_code == wx.WXK_RIGHT:
                self.reader.fastforward()
            elif key_code == wx.WXK_LEFT:
                self.reader.rewind()
            self.callback()
        if event.GetModifiers() == wx.MOD_ALT  and (key_code in (wx.WXK_HOME, wx.WXK_END)):
            pager = self.reader.active_section.pager
            if key_code == wx.WXK_HOME:
                to = pager.first
            elif key_code == wx.WXK_END:
                to = pager.last
            if to != self.reader.current_page:
                self.reader.current_page = to
                self.callback()
        if (self.zoom_callback is not None) and (
            event.GetModifiers() == wx.MOD_CONTROL
        ):
            if key_code in self.zoom_keymap:
                self.zoom_callback(self.zoom_keymap[key_code])

    @only_when_reader_ready
    def _text_ctrl_navigate_next(self, event):
        self.navigate_to_page(to="next")

    def navigate_to_page(self, to):
        rv = self.reader.navigate(to=to, unit="page")
        if not rv:
            if to == "prev":
                prev = self.reader.active_section.simple_prev
                if prev is not None and not prev.is_root:
                    self.reader.go_to_page(prev.pager.last)
            else:
                self.reader.navigate(to=to, unit="section")

    def _auto_navigate(self, key_code):
        now = time.time()
        last_press = self._key_press_record.get(key_code)
        num_lines = self.textCtrl.NumberOfLines - 1
        _curr_page = self.reader.current_page
        if (key_code == wx.WXK_UP):
            is_first_line = self.textCtrl.PositionToXY(self.textCtrl.InsertionPoint)[-1] == 0
            if not is_first_line:
                return
            if (last_press is not None) and (now - last_press) <= DKEY_TIMEOUT:
                self.navigate_to_page(to="prev")
                if _curr_page != self.reader.current_page:
                    self.textCtrl.InsertionPoint = self.textCtrl.GetLastPosition() - 1
            self._key_press_record[key_code] = now
        elif key_code == wx.WXK_DOWN:
            is_last_line = self.textCtrl.PositionToXY(self.textCtrl.InsertionPoint)[-1] == num_lines
            if not is_last_line:
                return
            if (last_press is not None) and (now - last_press) <= DKEY_TIMEOUT:
                self.navigate_to_page(to="next")
            self._key_press_record[key_code] = now

    def _reset_up_arrow_pressed_time(self, sender, current, prev):
        self._key_press_record.clear()