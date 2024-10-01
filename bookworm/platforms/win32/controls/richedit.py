# coding: utf-8

import ctypes
import queue
import threading
import time
from pathlib import Path

import win32api
import win32con
import wx

import bookworm.typehints as t
from bookworm import app, config
from bookworm.gui.text_ctrl_mixin import ContentViewCtrlMixin, ContentViewCtrlPanel
from bookworm.logger import logger
from bookworm.paths import app_path, libs_path

from .wnd_proc_hook import WndProcHookMixin

log = logger.getChild(__name__)


if app.is_frozen:
    BKWRICHEDITOPTS_DLL = libs_path("BkwRicheditOpts.dll")
else:
    BKWRICHEDITOPTS_DLL = (
        Path.cwd()
        / "scripts"
        / "dlls"
        / "richeditopts"
        / app.arch
        / "BkwRicheditOpts.dll"
    )


class WNDProcPanel(WndProcHookMixin, ContentViewCtrlPanel):
    """
    Custom panel that allows us to subscribe to Window Messages send for the parent.
    This is needed to allow us to track caret movements in a RichEdit Control.
    """

    def __init__(self, *args, **kwargs):
        ContentViewCtrlPanel.__init__(self, *args, **kwargs)
        WndProcHookMixin.__init__(self)
        self._dll = ctypes.cdll.LoadLibrary(str(BKWRICHEDITOPTS_DLL))
        self._event_queue = queue.PriorityQueue()
        self.hookWndProc()

    def init_caret_tracking(self):
        self._dll.Bkw_InitCaretTracking(self.text_ctrl.GetHandle())
        self.addMsgHandler(win32con.WM_NOTIFY, "WM_NOTIFY", self.onWM_NOTIFY)
        t = threading.Thread(
            target=self._tracking_thread,
            args=(
                self.text_ctrl,
                self._event_queue,
            ),
            daemon=True,
        )
        t.start()

    @staticmethod
    def _tracking_thread(text_ctrl, event_queue):
        CaretMoveEvent = text_ctrl.CaretMoveEvent
        parent = text_ctrl.GetTopLevelParent()
        text_ctrl_id = text_ctrl.GetId()
        last_pos = None
        while True:
            new_pos = event_queue.get()
            # Drop the earliest event since it rarely causes SegFault
            if last_pos is None:
                time.sleep(1)
                last_pos = -1
                continue
            if new_pos == last_pos:
                continue
            wx.PostEvent(parent, CaretMoveEvent(id=text_ctrl_id, Position=new_pos))
            last_pos = new_pos

    def onWM_NOTIFY(self, wParam, lParam):
        if (sel_loc := self._dll.Bkw_GetNewSelPos(ctypes.c_ssize_t(lParam))) >= 0:
            self._event_queue.put_nowait(sel_loc)
        return True


class ContentViewCtrl(ContentViewCtrlMixin):
    """Uses native win32 APIs to implement additional functionality."""

    ContainingPanel = WNDProcPanel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel.init_caret_tracking()

    def SetControlLabel(self, label_text: str) -> None:
        super().SetControlLabel(label_text)
        # Notify name change for the TextCtrl
        if config.conf["general"]["announce_ui_messages"]:
            ctypes.windll.user32.NotifyWinEvent(
                win32con.EVENT_OBJECT_NAMECHANGE,
                self.GetHandle(),
                win32con.OBJID_CLIENT,
                win32con.CHILDID_SELF,
            )
