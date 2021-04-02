# coding: utf-8

import wx
import wx.lib.newevent
from collections.abc import Container
from dataclasses import dataclass
from itertools import chain
import bookworm.typehints as t
from bookworm.structured_text import SemanticElementType
from bookworm.logger import logger


log = logger.getChild(__name__)
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
SEMANTIC_MAP = {
    "H": SemanticElementType.HEADING,
    "K": SemanticElementType.LINK,
    "L": SemanticElementType.LIST,
    "T": SemanticElementType.TABLE,
    "C": SemanticElementType.CODE_BLOCK,
    "Q": SemanticElementType.QUOTE,
}
SEMANTIC_KEY_MAP = {ord(k): v for k, v in SEMANTIC_MAP.items()}
    

@dataclass
class SelectionRange(Container):
    """Represents a text range in an edit control."""

    start: int
    end: int

    def __contains__(self, x):
        return self.start <= x <= self.end

    def __iter__(self):
        return iter((self.start, self.end))


class ContentViewCtrl(wx.TextCtrl):
    """
    Provides a unified method to capture context menu requests in TextCtrl's.
    Also contains some work arounds.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            style=wx.TE_READONLY
            | wx.TE_MULTILINE
            | wx.TE_RICH2
            | wx.TE_AUTO_URL
            | wx.TE_NOHIDESEL,
            **kwargs
        )

    def GetContainingLine(self, position):
        _, col, lino = self.PositionToXY(position)
        left = position - col
        return (left, left + self.GetLineLength(lino))

    def TryBefore(self, event):
        """Prehandling of events."""
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
        ):
            wx.QueueEvent(self, StructuredNavigationEvent(
                SemanticElementType=SEMANTIC_KEY_MAP[keycode],
                Forward=not event.ShiftDown()
            ))
            return True
        return super().TryBefore(event)
