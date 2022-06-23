# coding: utf-8

import time

import wx

from bookworm import config, speech
from bookworm.document import PaginationError
from bookworm.gui.contentview_ctrl import (EVT_CONTENT_NAVIGATION,
                                           EVT_STRUCTURED_NAVIGATION,
                                           NAV_BACKWORD_KEYS,
                                           NAV_FOREWORD_KEYS, NAVIGATION_KEYS)
from bookworm.logger import logger
from bookworm.signals import reader_page_changed

log = logger.getChild(__name__)
# Time_out of consecutive key presses in seconds
DKEY_TIMEOUT = 0.75
LINK_ACTIVATION_KEYS = {wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER}
# Paginate by how many characters
PAGINATION_NUM_CHARS = 2000  # typical number of chars per page in English documents


class NavigationProvider:
    """Implements keyboard navigation for viewer controls."""

    def __init__(self, ctrl, reader, callback_func=None, zoom_callback=None, view=None):
        self._nav_ctrl = ctrl
        self.reader = reader
        self.callback_func = callback_func
        self.zoom_callback = zoom_callback
        self.view = view
        self._key_press_record = {}
        if self.zoom_callback:
            self.zoom_keymap = {ord("0"): 0, ord("="): 1, ord("-"): -1}
        ctrl.Bind(wx.EVT_KEY_UP, self.onKeyUp, ctrl)
        if isinstance(ctrl, wx.TextCtrl):
            ctrl.Bind(EVT_CONTENT_NAVIGATION, self.onTextCtrlNavigate)
            ctrl.Bind(EVT_STRUCTURED_NAVIGATION, self.onStructuredNavigation)
        reader_page_changed.connect(self._reset_up_arrow_pressed_time, weak=False)

    def callback(self):
        if self.callback_func is not None:
            return self.callback_func()

    def onKeyUp(self, event):
        event.Skip()
        if not self.reader.ready:
            return
        key_code = event.GetKeyCode()
        if isinstance(self._nav_ctrl, wx.TextCtrl) and key_code in {
            wx.WXK_UP,
            wx.WXK_DOWN,
        }:
            self._auto_navigate(event, key_code)
        elif key_code in NAVIGATION_KEYS:
            if key_code in NAV_FOREWORD_KEYS:
                if self.reader.document.supports_links():
                    modifiers = event.GetModifiers()
                    if modifiers == wx.MOD_CONTROL:
                        self.try_handle_special_actions()
                        return
                    elif modifiers == wx.MOD_CONTROL | wx.MOD_SHIFT:
                        self.reader.pop_navigation_stack()
                        return
                self.reader.go_to_next()
            elif key_code in NAV_BACKWORD_KEYS:
                self.reader.go_to_prev()
            self.callback()
        elif isinstance(self._nav_ctrl, wx.TextCtrl) and key_code == wx.WXK_PAGEDOWN:
            self._do_paginate(self._nav_ctrl, down=True)
        elif isinstance(self._nav_ctrl, wx.TextCtrl) and key_code == wx.WXK_PAGEUP:
            self._do_paginate(self._nav_ctrl, down=False)
        if event.GetModifiers() == wx.MOD_ALT and key_code in (
            wx.WXK_PAGEUP,
            wx.WXK_PAGEDOWN,
        ):
            if key_code == wx.WXK_PAGEDOWN:
                self.reader.navigate(to="next", unit="section")
            elif key_code == wx.WXK_PAGEUP:
                self.reader.navigate(to="prev", unit="section")
            self.callback()
            return
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

    def onTextCtrlNavigate(self, event):
        if not self.reader.ready:
            return
        keycode = event.KeyCode
        if keycode in NAV_FOREWORD_KEYS:
            self.reader.go_to_next()
        elif keycode in NAV_BACKWORD_KEYS:
            self.reader.go_to_prev()
        else:
            raise ValueError(f"KeyCode: {keycode} is not a content navigation key")

    def _auto_navigate(self, event, key_code):
        now = time.time()
        last_press = self._key_press_record.get(key_code)
        num_lines = self._nav_ctrl.NumberOfLines - 1
        _curr_page = self.reader.current_page
        if key_code == wx.WXK_UP:
            is_first_line = (
                self._nav_ctrl.PositionToXY(self._nav_ctrl.InsertionPoint)[-1] == 0
            )
            if not is_first_line:
                return
            if (last_press is not None) and (now - last_press) <= DKEY_TIMEOUT:
                self.reader.go_to_prev()
                if _curr_page != self.reader.current_page:
                    self._nav_ctrl.InsertionPoint = self._nav_ctrl.GetLastPosition() - 1
            self._key_press_record[key_code] = now
        elif key_code == wx.WXK_DOWN:
            is_last_line = (
                self._nav_ctrl.PositionToXY(self._nav_ctrl.InsertionPoint)[-1]
                == num_lines
            )
            if not is_last_line:
                return
            if (last_press is not None) and (now - last_press) <= DKEY_TIMEOUT:
                self.reader.go_to_next()
            self._key_press_record[key_code] = now

    def onStructuredNavigation(self, event):
        if not self.reader.ready:
            wx.Bell()
            return
        elif not self.reader.document.supports_structural_navigation():
            # Translators: spoken message when the current document does not
            # support structural navigation
            speech.announce("Not supported in this document.")
            return
        self.view.navigate_to_structural_element(
            element_type=event.SemanticElementType, forward=event.Forward
        )

    def _reset_up_arrow_pressed_time(self, sender, current, prev):
        self._key_press_record.clear()

    def try_handle_special_actions(self):
        return self.reader.handle_special_action_for_position(
            self.view.get_insertion_point()
        )

    def _do_paginate(self, text_ctrl, down):
        current_pos = self.view.get_containing_line(text_ctrl.GetInsertionPoint())[0]
        if down:
            target_pos = current_pos + PAGINATION_NUM_CHARS
            if target_pos >= (last_pos := text_ctrl.GetLastPosition()):
                text_ctrl.SetInsertionPoint(last_pos - 1)
                return
        else:
            target_pos = current_pos - PAGINATION_NUM_CHARS
            if target_pos < PAGINATION_NUM_CHARS:
                target_pos = 0
        target_fol = self.view.get_containing_line(
            round(target_pos / PAGINATION_NUM_CHARS) * PAGINATION_NUM_CHARS
        )[0]
        text_ctrl.SetInsertionPoint(target_fol)
