import ctypes
import queue
import threading
import time
from pathlib import Path

import win32con
import wx

from bookworm import app, config
from bookworm.gui.text_ctrl_mixin import ContentViewCtrlMixin, ContentViewCtrlPanel
from bookworm.logger import logger
from bookworm.paths import libs_path

from .wnd_proc_hook import WndProcHookMixin

log = logger.getChild(__name__)
# CHARFORMATW.szFaceName has 32 UTF-16 code units, including its trailing NUL.
_MAX_RICHEDIT_FACE_NAME_CODE_UNITS = 31
_TEXT_FONT_ARGTYPES = (
    ctypes.c_ssize_t,
    ctypes.POINTER(ctypes.c_uint16),
    ctypes.c_uint32,
    ctypes.c_int,
    ctypes.c_int,
)


def _configure_dll_function(dll, name, argtypes, *, required=False):
    try:
        func = getattr(dll, name)
    except AttributeError:
        if required:
            raise
        return None
    func.argtypes = argtypes
    func.restype = ctypes.c_int
    return func


if app.is_frozen:
    BKWRICHEDITOPTS_DLL = libs_path("BkwRicheditOpts.dll")
else:
    BKWRICHEDITOPTS_DLL = (
        Path.cwd() / "scripts" / "dlls" / "richeditopts" / app.arch / "BkwRicheditOpts.dll"
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
        self._init_caret_tracking = _configure_dll_function(
            self._dll,
            "Bkw_InitCaretTracking",
            (ctypes.c_ssize_t,),
            required=True,
        )
        self._get_new_sel_pos = _configure_dll_function(
            self._dll,
            "Bkw_GetNewSelPos",
            (ctypes.c_ssize_t,),
            required=True,
        )
        self._set_all_text_font = _configure_dll_function(
            self._dll,
            "Bkw_SetAllTextFont",
            _TEXT_FONT_ARGTYPES,
        )
        self._set_default_text_font = _configure_dll_function(
            self._dll,
            "Bkw_SetDefaultTextFont",
            _TEXT_FONT_ARGTYPES,
        )
        self._set_all_text_point_size = _configure_dll_function(
            self._dll,
            "Bkw_SetAllTextPointSize",
            (ctypes.c_ssize_t, ctypes.c_int),
        )
        self._event_queue = queue.PriorityQueue()
        self.hookWndProc()

    def init_caret_tracking(self):
        self._init_caret_tracking(self.text_ctrl.GetHandle())
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
        if (sel_loc := self._get_new_sel_pos(lParam)) >= 0:
            self._event_queue.put_nowait(sel_loc)
        return True

    def _call_text_font_formatter(self, formatter, font: wx.Font) -> bool:
        if formatter is None or not font.IsOk():
            return False
        face_name = font.GetFaceName()
        try:
            encoded_face_name = face_name.encode("utf-16-le")
        except UnicodeEncodeError:
            return False
        face_length = len(encoded_face_name) // 2
        if not 0 < face_length <= _MAX_RICHEDIT_FACE_NAME_CODE_UNITS:
            return False
        face_buffer = (ctypes.c_uint16 * (face_length + 1))()
        ctypes.memmove(face_buffer, encoded_face_name, len(encoded_face_name))
        return (
            formatter(
                self.text_ctrl.GetHandle(),
                face_buffer,
                face_length,
                font.GetPointSize(),
                int(font.GetWeight() >= wx.FONTWEIGHT_BOLD),
            )
            == 1
        )

    def set_all_text_font(self, font: wx.Font) -> bool:
        return self._call_text_font_formatter(self._set_all_text_font, font)

    def set_default_text_font(self, font: wx.Font) -> bool:
        return self._call_text_font_formatter(self._set_default_text_font, font)

    def set_all_text_point_size(self, point_size: int) -> bool:
        if self._set_all_text_point_size is None:
            return False
        return self._set_all_text_point_size(self.text_ctrl.GetHandle(), point_size) == 1


class ContentViewCtrl(ContentViewCtrlMixin):
    """Uses native win32 APIs to implement additional functionality."""

    ContainingPanel = WNDProcPanel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel.init_caret_tracking()

    def _warn_native_fallback_once(self, operation: str) -> None:
        warned_operations = getattr(self, "_native_fallback_warnings", set())
        if operation in warned_operations:
            return
        warned_operations.add(operation)
        self._native_fallback_warnings = warned_operations
        log.warning("Native RichEdit %s formatting failed; using wx fallback", operation)

    def set_all_text_font(self, font: wx.Font) -> bool:
        if self.panel.set_all_text_font(font):
            return True
        self._warn_native_fallback_once("font")
        return super().set_all_text_font(font)

    def set_default_text_font(self, font: wx.Font) -> bool:
        if self.panel.set_default_text_font(font):
            return True
        self._warn_native_fallback_once("default-font")
        return super().set_default_text_font(font)

    def set_all_text_point_size(self, point_size: int) -> bool:
        if self.panel.set_all_text_point_size(point_size):
            return True
        self._warn_native_fallback_once("point-size")
        return super().set_all_text_point_size(point_size)

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
