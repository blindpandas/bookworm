# coding: utf-8

import wx
from bookworm.logger import logger
from .decorators import only_when_reader_ready


class NavigationProvider:
    """Implements keyboard navigation for viewer controls."""

    def __init__(self, ctrl, reader, callback_func=None, zoom_callback=None):
        self.reader = reader
        self.callback_func = callback_func
        self.zoom_callback = zoom_callback
        if self.zoom_callback:
            self.zoom_keymap = {ord("0"): 0, ord("="): 1, ord("-"): -1}
        ctrl.Bind(wx.EVT_KEY_UP, self.onKeyUp, ctrl)
        # Funky  thinks can happen if we use normal `Key up` event with wx.TextCtrl
        if isinstance(ctrl, wx.TextCtrl):
            ctrl.Bind(wx.EVT_TEXT_ENTER, self._text_ctrl_navigate_next, ctrl)

    def callback(self):
        if self.callback_func is not None:
            return self.callback_func()

    @only_when_reader_ready
    def onKeyUp(self, event):
        event.Skip()
        key_code = event.GetKeyCode()
        if key_code in (wx.WXK_RETURN, wx.WXK_BACK):
            if (
                not isinstance(event.GetEventObject(), wx.TextCtrl)
                and key_code == wx.WXK_RETURN
            ):
                self.reader.navigate(to="next", unit="page")
            elif key_code == wx.WXK_BACK:
                self.reader.navigate(to="prev", unit="page")
            self.callback()
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
        elif key_code in (wx.WXK_HOME, wx.WXK_END):
            pager = self.reader.active_section.pager
            if key_code == wx.WXK_HOME:
                to = pager.first
            elif key_code == wx.WXK_END:
                to = pager.last
            if to != self.reader.current_page:
                self.reader.current_page = to
                self.callback()
        elif (self.zoom_callback is not None) and (
            event.GetModifiers() == wx.MOD_CONTROL
        ):
            if key_code in self.zoom_keymap:
                self.zoom_callback(self.zoom_keymap[key_code])

    @only_when_reader_ready
    def _text_ctrl_navigate_next(self, event):
        self.reader.navigate(to="next", unit="page")
