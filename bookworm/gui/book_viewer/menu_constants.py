# coding: utf-8

import enum
import itertools
import wx


ID_GEN = itertools.count(start=14004, step=5)


class BookRelatedMenuIds(enum.IntEnum):
    """Declares  menu ids for items which are enabled/disabled
    based on whether a book is loaded or not.
    """

    # File
    export = wx.ID_SAVEAS
    pin_document = next(ID_GEN)
    closeCurrentFile = next(ID_GEN)
    # Document
    document_summary = next(ID_GEN)
    element_list = next(ID_GEN)
    # Tools
    goToPage = next(ID_GEN)
    goToPageByLabel = next(ID_GEN)
    searchBook = wx.ID_FIND
    findNext = next(ID_GEN)
    findPrev = next(ID_GEN)
    viewRenderedAsImage = next(ID_GEN)
    changeReadingMode = next(ID_GEN)


class ViewerMenuIds(enum.IntEnum):
    """Declares menu ids for all other menu items."""

    # Tools menu
    preferences = wx.ID_PREFERENCES
    # Help Menu
    documentation = next(ID_GEN)
    website = next(ID_GEN)
    license = next(ID_GEN)
    contributors = next(ID_GEN)
    restart_with_debug = next(ID_GEN)
    about = next(ID_GEN)


KEYBOARD_SHORTCUTS = {
    wx.ID_OPEN: "Ctrl-O",
    BookRelatedMenuIds.pin_document: "Ctrl-P",
    BookRelatedMenuIds.closeCurrentFile: "Ctrl-W",
    BookRelatedMenuIds.element_list: "Ctrl+F7",
    BookRelatedMenuIds.goToPage: "Ctrl-G",
    wx.ID_FIND: "Ctrl-F",
    BookRelatedMenuIds.findNext: "F3",
    BookRelatedMenuIds.findPrev: "Shift-F3",
    BookRelatedMenuIds.viewRenderedAsImage: "Ctrl-R",
    BookRelatedMenuIds.changeReadingMode: "Ctrl-Shift-M",
    wx.ID_PREFERENCES: "Ctrl-Shift-P",
    ViewerMenuIds.documentation: "F1",
}
