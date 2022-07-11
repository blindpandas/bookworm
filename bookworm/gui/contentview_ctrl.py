# coding: utf-8

import struct
import time
from itertools import chain

import winsound

import queue
import threading

import ctypes

import win32api
import win32con
import win32gui
import win32gui_struct
import winsound
import wx
import wx.lib.newevent

import bookworm.typehints as t
from bookworm.logger import logger
from bookworm.structured_text import SemanticElementType
from bookworm.gui.wnd_proc_hook import WndProcHookMixin

log = logger.getChild(__name__)




EM_GETEVENTMASK = win32con.WM_USER + 59
EM_SETEVENTMASK = win32con.WM_USER + 69

CaretMoveEvent, EVT_CARET= wx.lib.newevent.NewEvent()
ContextMenuEvent, EVT_CONTEXTMENU_REQUESTED = wx.lib.newevent.NewCommandEvent()
ContentNavigationEvent, EVT_CONTENT_NAVIGATION = wx.lib.newevent.NewEvent()
StructuredNavigationEvent, EVT_STRUCTURED_NAVIGATION = wx.lib.newevent.NewEvent()
NAV_FOREWORD_KEYS = {
    wx.WXK_SPACE,
    wx.WXK_RETURN,
    wx.WXK_NUMPAD_ENTER,
}
NAV_BACKWORD_KEYS = {
    wx.WXK_BACK,
}
NAVIGATION_KEYS = NAV_FOREWORD_KEYS.union(NAV_BACKWORD_KEYS)
HEADING_LEVEL_KEY_MAP = {
    "1": SemanticElementType.HEADING_1,
    "2": SemanticElementType.HEADING_2,
    "3": SemanticElementType.HEADING_3,
    "4": SemanticElementType.HEADING_4,
    "5": SemanticElementType.HEADING_5,
    "6": SemanticElementType.HEADING_6,
}
SEMANTIC_MAP = {
    "H": SemanticElementType.HEADING,
    "K": SemanticElementType.LINK,
    "L": SemanticElementType.LIST,
    "T": SemanticElementType.TABLE,
    "Q": SemanticElementType.QUOTE,
    # "G": SemanticElementType.FIGURE,
}
SEMANTIC_MAP |= HEADING_LEVEL_KEY_MAP
SEMANTIC_KEY_MAP = {ord(k): v for k, v in SEMANTIC_MAP.items()}


class NMHDR(ctypes.Structure):
    _fields_ = [
        ("hwndFrom", ctypes.wintypes.HWND),
        ("idFrom", ctypes.wintypes.UINT),
        ("code", ctypes.c_int)
    ]


class CHARRANGE(ctypes.Structure):
    _fields_ = [
        ("cpMin", ctypes.wintypes.LONG),
        ("cpMax", ctypes.wintypes.LONG),
    ]


class SELCHANGE(ctypes.Structure):
    _fields_ = [
        ("nmhdr", NMHDR),
        ("chrg", CHARRANGE),
        ("seltyp", ctypes.wintypes.WORD),
    ]




class WNDProcPanel(WndProcHookMixin, wx.Panel):
    """
    Custom panel that allows us to subscribe to win32 Window Messages.
    This is needed to allow us to track caret movements in a RichEdit Control.
    """

    def __init__(self, text_ctrl, *args, **kwargs):
        super(wx.Panel, self).__init__(*args, **kwargs)
        WndProcHookMixin.__init__(self)
        self.text_ctrl = text_ctrl
        self._event_queue = queue.Queue()
        self.hookWndProc()

    def init_caret_tracking(self):
        text_ctrl_handle = self.text_ctrl.GetHandle()
        # First retrieve the current event mask
        current_event_mask = win32api.SendMessage(text_ctrl_handle, EM_GETEVENTMASK, 0, 0)
        win32api.SendMessage(
            text_ctrl_handle,
            EM_SETEVENTMASK,
            0,
            current_event_mask | win32con.ENM_SELCHANGE
        )
        self.addMsgHandler(win32con.WM_NOTIFY , "WM_NOTIFY", self.onWM_NOTIFY)
        t = threading.Thread(target=self._tracking_thread, daemon=True)
        t.start()

    def _tracking_thread(self):
        last_pos = 0
        reader = wx.GetApp().mainFrame.reader
        text_ctrl = self.text_ctrl
        event_queue = self._event_queue
        while True:
            new_pos = event_queue.get()
            if new_pos == last_pos:
                continue
            if new_pos == text_ctrl.GetLastPosition():
                wx.CallAfter(reader.go_to_next)
                continue
            #wx.QueueEvent(self.text_ctrl, CaretMoveEvent(Position=new_pos))
            last_pos = new_pos

    def onWM_NOTIFY(self, wParam, lParam):
        hwndFrom, idFrom, code = win32gui_struct.UnpackWMNOTIFY(lParam)
        if code == win32con.EN_SELCHANGE:
            st = SELCHANGE.from_address(lParam)
            log.info(f"{st.nmhdr.code=}")
            if st.seltyp == win32con.SEL_EMPTY:
                self._event_queue.put_nowait(st.chrg.cpMin)
        return True



class ContentViewCtrl(wx.TextCtrl):
    """
    Provides a unified method to capture context menu requests in TextCtrl's.
    Also contains some hacks to work arounds wxWidget's limitations.
    """

    def __init__(self, parent, *args, **kwargs):
        panel = WNDProcPanel(self, parent, size=parent.GetSize())
        super().__init__(
            panel,
            *args,
            style=wx.TE_READONLY
            | wx.TE_MULTILINE
            | wx.TE_RICH2
            | wx.TE_AUTO_URL
            | wx.TE_NOHIDESEL,
            **kwargs,
        )
        panel.init_caret_tracking()

    def GetContainingLine(self, position):
        _, col, lino = self.PositionToXY(position)
        left = position - col
        return (left, left + self.GetLineLength(lino))

    def TryBefore(self, event):
        """Pre-handling of events."""
        evtType = event.GetEventType()
        if evtType == wx.EVT_CONTEXT_MENU.typeId:
            wx.PostEvent(self, ContextMenuEvent(self.GetId(), fromMouse=False))
            return True
        elif evtType == wx.EVT_RIGHT_UP.typeId:
            wx.PostEvent(self, ContextMenuEvent(self.GetId(), fromMouse=True))
            return True
        elif evtType == wx.EVT_KEY_UP.typeId and (
            event.GetKeyCode() == wx.WXK_WINDOWS_MENU
        ):
            # This event is redundant
            return True
        elif (
            isinstance(event, wx.KeyEvent)
            and not event.HasAnyModifiers()
            and event.GetKeyCode() in NAVIGATION_KEYS
        ):
            if evtType == wx.EVT_CHAR_HOOK.typeId:
                wx.QueueEvent(self, ContentNavigationEvent(KeyCode=event.GetKeyCode()))
            return True
        elif (
            evtType == wx.EVT_CHAR_HOOK.typeId
            and (keycode := event.GetKeyCode()) in SEMANTIC_KEY_MAP
            and not event.ControlDown()
            and not event.AltDown()
        ):
            wx.QueueEvent(
                self,
                StructuredNavigationEvent(
                    SemanticElementType=SEMANTIC_KEY_MAP[keycode],
                    Forward=not event.ShiftDown(),
                ),
            )
            return True
        return super().TryBefore(event)
