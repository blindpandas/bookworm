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
        kwargs.setdefault('size', (1200, 750))
        super().__init__(parent=parent, title=title, **kwargs)
        self.make_controls()
        self.Maximize()
        self.CenterOnScreen()

    @classmethod
    def show_standalone(cls, database_file):
        app = wx.App()
        bookshelf_window = cls(None, title=_("Bookworm Bookshelf"))
        bookshelf_window.Show()
        app.MainLoop()

    def make_controls(self):
        panel = self.GetContentsPane()
        panel.SetSizerType('horizontal')
        lhs_panel = sc.SizedPanel(panel)
        lhs_panel.SetSizerType('vertical')
        wx.StaticText(lhs_panel, -1, _("Provider"))
        provider_choice = wx.Choice(lhs_panel, -1, choices=['Local Bookshelf', 'Pocket', 'Google Drive', 'OneDrive', 'Dropbox',])
        wx.StaticText(lhs_panel, -1, _("Categories"))
        self.tree_tabs = BookshelfNoteBook(lhs_panel, -1)
        tree_ctrl = self.tree_tabs.GetTreeCtrl()
        tree_ctrl.SetMinSize((120, -1))
        tree_ctrl.SetLabel(_("Categories"))
        self.tree_tabs.AddPage(BookshelfResultsPage(self.tree_tabs, -1, query=None), "Hello")
        self.tree_tabs.GetTreeCtrl().SetLabel(_("Shelfs"))
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGING, self.OnPageChanging)

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        print('OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()

