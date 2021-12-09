# coding: utf-8


import wx
import wx.lib.sized_controls as sc
from enum import IntEnum, auto
from bookworm.gui.components import ImmutableObjectListView, ColumnDefn
from bookworm.logger import logger


log = logger.getChild(__name__)


class BookshelfResultsPage(sc.SizedPanel):

    def __init__(self, parent, id, query):
        super().__init__(parent, id)
        self.query = query
        wx.Button(self, -1, _("Hey"))
        self.book_list = wx.ListCtrl(self, -1)


class BookshelfNoteBook(wx.Treebook):

    def __init__(self, parent, id):
        super().__init__(parent, id)


class BookshelfWindow(sc.SizedFrame):

    def __init__(self, parent, title, **kwargs):
        kwargs.setdefault('size', (750, 840))
        super().__init__(parent=parent, title=title, **kwargs)
        self.make_controls()
        # Center
        if self.GetParent() is not None:
            self.CenterOnParent()
        else:
            self.CenterOnScreen()

    def make_controls(self):
        panel = self.GetContentsPane()
        panel.SetSizerType('horizontal')
        self.tree_tabs = BookshelfNoteBook(panel, -1)
        self.tree_tabs.AddPage(BookshelfResultsPage(self.tree_tabs, -1, query=None), "Hello")
        self.tree_tabs.GetTreeCtrl().SetLabel(_("Shelfs"))
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGING, self.OnPageChanging)

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        print('OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()

