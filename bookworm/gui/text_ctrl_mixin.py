# coding: utf-8

import wx
import wx.lib.newevent

import bookworm.typehints as t
from bookworm.logger import logger
from bookworm.structured_text import SemanticElementType
from bookworm import config

log = logger.getChild(__name__)


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


class ContentViewCtrlPanel(wx.Panel):
    def __init__(self, text_ctrl, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_ctrl = text_ctrl


class ContentViewCtrlMixin(wx.TextCtrl):
    """
    Adds new events, and customizes some default behaviors to `wx.TextCtrl`.
    This class may have platform specific subclasses.
    """

    ContainingPanel = ContentViewCtrlPanel
    CaretMoveEvent, EVT_CARET = wx.lib.newevent.NewCommandEvent()
    ContextMenuEvent, EVT_CONTEXTMENU_REQUESTED = wx.lib.newevent.NewCommandEvent()
    ContentNavigationEvent, EVT_CONTENT_NAVIGATION = wx.lib.newevent.NewEvent()
    StructuredNavigationEvent, EVT_STRUCTURED_NAVIGATION = wx.lib.newevent.NewEvent()
    TEXTCTRL_STYLE = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_NOHIDESEL

    def __init__(self, parent, *args, label="", **kwargs):
        self.panel = self.ContainingPanel(self, parent, size=parent.GetSize())
        self.controlLabel = wx.StaticText(self.panel, -1, label)
        style = self.TEXTCTRL_STYLE
        if not config.conf["appearance"]["text_wrap"]:
            style |= wx.TE_DONTWRAP
        super().__init__(
            self.panel,
            *args,
            style=style,
            **kwargs,
        )
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.controlLabel)
        vsizer.Add(self, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(vsizer, 1, wx.EXPAND | wx.ALL)
        self.panel.SetSizer(sizer)
        sizer.Fit(self.panel)

    def SetControlLabel(self, label_text: str) -> None:
        self.controlLabel.SetLabel(label_text)

    def GetContainingLine(self, position):
        _, col, lino = self.PositionToXY(position)
        left = position - col
        return (left, left + self.GetLineLength(lino))

    def TryBefore(self, event):
        """Pre-handling of events."""
        evtType = event.GetEventType()
        if evtType == wx.EVT_CONTEXT_MENU.typeId:
            wx.PostEvent(self, self.ContextMenuEvent(self.GetId(), fromMouse=False))
            return True
        elif evtType == wx.EVT_RIGHT_UP.typeId:
            wx.PostEvent(self, self.ContextMenuEvent(self.GetId(), fromMouse=True))
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
                wx.QueueEvent(
                    self, self.ContentNavigationEvent(KeyCode=event.GetKeyCode())
                )
            return True
        elif (
            evtType == wx.EVT_CHAR_HOOK.typeId
            and (keycode := event.GetKeyCode()) in SEMANTIC_KEY_MAP
            and not event.ControlDown()
            and not event.AltDown()
        ):
            wx.QueueEvent(
                self,
                self.StructuredNavigationEvent(
                    SemanticElementType=SEMANTIC_KEY_MAP[keycode],
                    Forward=not event.ShiftDown(),
                ),
            )
            return True
        return super().TryBefore(event)
