# coding: utf-8

import winsound
import time
import os
import ctypes
import ctypes.wintypes
import weakref
import threading
import win32con
import wx
import wx.lib.newevent
from bookworm.signals import app_started, app_shuttingdown
from bookworm.logger import logger


log = logger.getChild(__name__)

file = open("log.txt", "w")
user32 = ctypes.windll.user32
ole32 = ctypes.windll.ole32
user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

_listen_for_windows_events = threading.Event()
TRACKED_INSTANCES = weakref.WeakSet()
LAST_EVENT_TIME = {}
LAST_KNOWN_POSITIONS = {}
# Custom wx event
CaretMoveEvent, EVT_CARET_MOVE = wx.lib.newevent.NewCommandEvent()
# The Windows event we're interested in
CARET_TRACKER_HOOK_HANDLE = None
EVENT_OBJECT_TEXTSELECTIONCHANGED = 0x8014
WINEVENT_OUTOFCONTEXT = 0x0000
OBJID_CARET = win32con.OBJID_CARET
WinEventProcType = ctypes.WINFUNCTYPE(
    None, 
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD
)


def init_caret_tracking(control_instance: wx.Window):
    TRACKED_INSTANCES.add(control_instance)




def callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
    global LAST_EVENT_TIME
    if idObject == win32con.OBJID_CLIENT:
        for control in TRACKED_INSTANCES:
            if control and (control.GetHandle() == hwnd):
                if control.GetInsertionPoint() == control.GetLastPosition():
                    wx.PostEvent(control, CaretMoveEvent(control.GetId()))
                    time.sleep(2)



@app_started.connect
def register_caret_tracking_hook(sender):
    global CARET_TRACKER_HOOK_HANDLE 

    def listen_for_messages():
        ole32.CoInitialize(0)
        WinEventProc = WinEventProcType(callback)
        CARET_TRACKER_HOOK_HANDLE = user32.SetWinEventHook(
            EVENT_OBJECT_TEXTSELECTIONCHANGED,
            EVENT_OBJECT_TEXTSELECTIONCHANGED,
            0,
            WinEventProc,
            ctypes.c_long(os.getpid()),
            ctypes.c_long(threading.main_thread().ident),
            win32con.WINEVENT_OUTOFCONTEXT
        )
        _listen_for_windows_events.set()
        msg = ctypes.wintypes.MSG()
        while _listen_for_windows_events.is_set() and user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.DispatchMessageW(msg)

    t = threading.Thread(target=listen_for_messages, daemon=True)
    t.start()


@app_shuttingdown.connect
def _stop_event_listener(sender):
    _listen_for_windows_events.clear()
    user32.UnhookWinEvent(CARET_TRACKER_HOOK_HANDLE)
    ole32.CoUninitialize()
