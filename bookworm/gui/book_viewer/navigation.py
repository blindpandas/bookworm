# coding: utf-8

import time
import wx
from bookworm import config
from bookworm.document_formats import PaginationError
from bookworm.signals import reader_page_changed
from bookworm.logger import logger


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
            ctrl.Bind(wx.EVT_TEXT_ENTER, self.onTextCtrlNavigateNext, ctrl)

    def callback(self):
        if self.callback_func is not None:
            return self.callback_func()

    def onKeyUp(self, event):
        event.Skip()
        if not self.reader.ready:
            return
        key_code = event.GetKeyCode()
        if isinstance(event.GetEventObject(), wx.TextCtrl) and key_code in (
            wx.WXK_UP,
            wx.WXK_DOWN,
        ):
            self._auto_navigate(key_code)
        elif key_code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_BACK):
            if not isinstance(event.GetEventObject(), wx.TextCtrl) and key_code in (
                wx.WXK_RETURN,
                wx.WXK_NUMPAD_ENTER,
            ):
                self.reader.go_to_next()
            elif key_code == wx.WXK_BACK:
                self.reader.go_to_prev()
            self.callback()
        elif (
            isinstance(event.GetEventObject(), wx.TextCtrl)
            and key_code == wx.WXK_PAGEDOWN
        ):
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
        if event.GetModifiers() == wx.MOD_ALT and (
            key_code in (wx.WXK_HOME, wx.WXK_END)
        ):
            if key_code == wx.WXK_HOME:
                self.reader.go_to_first_of_section()
            elif key_code == wx.WXK_END:
                self.reader.go_to_last_of_section()
            self.callback()
        if (self.zoom_callback is not None) and (
            event.GetModifiers() == wx.MOD_CONTROL
        ):
            if key_code in self.zoom_keymap:
                self.zoom_callback(self.zoom_keymap[key_code])

    def onTextCtrlNavigateNext(self, event):
        if self.reader.ready:
            self.reader.go_to_next()

    def _auto_navigate(self, key_code):
        now = time.time()
        last_press = self._key_press_record.get(key_code)
        num_lines = self.textCtrl.NumberOfLines - 1
        _curr_page = self.reader.current_page
        if key_code == wx.WXK_UP:
            is_first_line = (
                self.textCtrl.PositionToXY(self.textCtrl.InsertionPoint)[-1] == 0
            )
            if not is_first_line:
                return
            if (last_press is not None) and (now - last_press) <= DKEY_TIMEOUT:
                self.reader.go_to_prev()
                if _curr_page != self.reader.current_page:
                    self.textCtrl.InsertionPoint = self.textCtrl.GetLastPosition() - 1
            self._key_press_record[key_code] = now
        elif key_code == wx.WXK_DOWN:
            is_last_line = (
                self.textCtrl.PositionToXY(self.textCtrl.InsertionPoint)[-1]
                == num_lines
            )
            if not is_last_line:
                return
            if (last_press is not None) and (now - last_press) <= DKEY_TIMEOUT:
                self.reader.go_to_next()
            self._key_press_record[key_code] = now

    def _reset_up_arrow_pressed_time(self, sender, current, prev):
        self._key_press_record.clear()
