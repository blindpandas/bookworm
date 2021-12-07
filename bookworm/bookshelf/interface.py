# coding: utf-8


import winsound
import wx
import wx.lib.sized_controls as sc
from enum import IntEnum, auto
from bookworm.gui.components import ImmutableObjectListView, ColumnDefn
from bookworm.gui.settings import SettingsPanel, ReconciliationStrategies
from bookworm.logger import logger


log = logger.getChild(__name__)


class StatefulBookshelfMenuIds(IntEnum):
    add_current_book_to_shelf = 25001
    remove_current_book_from_shelf = 25002


class StatelessBookshelfMenuIds(IntEnum):
    open_bookshelf = 25100
    create_new_category = 25101


class BookshelfResultsPage(sc.SizedPanel):

    def __init__(self, parent, id, query):
        super().__init__(parent, id)
        self.query = query
        self.book_list = ImmutableObjectListView(self, -1)


class BookshelfNoteBook(wx.Treebook):

    def __init__(self, parent, id):
        super().__init__(parent, id)


class BookshelfWindow(sc.SizedFrame):

    def __init__(self, parent, title, **kwargs):
        super().__init__(parent=parent, title=title, **kwargs)
        self.make_controls()
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGING, self.OnPageChanging)

    def make_controls(self):
        panel = self.GetContentsPane()
        panel.SetSizerType('horizontal')
        self.tree_tabs = BookshelfNoteBook(panel, -1)
        self.tree_tabs.AddPage(BookshelfResultsPage(self, -1, query=None))

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        print('OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()


class BookshelfSettingsPanel(SettingsPanel):
    config_section = "bookshelf"

    def addControls(self):
        # Translators: the label of a group of controls in the reading page
        generalReadingBox = self.make_static_box(_("Bookshelf"))
        wx.CheckBox(
            generalReadingBox,
            -1,
            # Translators: the label of a checkbox
            _("Automatically add opened books to the bookshelf"),
            name="bookshelf.auto_add_opened_documents_to_bookshelf",
        )


class BookshelfMenu(wx.Menu):

    def __init__(self, service, menubar):
        super().__init__()
        self.service = service
        self.menubar = menubar
        self.view = service.view
        self.Append(
            StatelessBookshelfMenuIds.open_bookshelf,
            # Translators: the label of an item in the application menubar
            _("&Open Bookshelf"),
            # Translators: the help text of an item in the application menubar
            _("Open your bookshelf"),
        )
        self.Append(
            StatefulBookshelfMenuIds.add_current_book_to_shelf,
            # Translators: the label of an item in the application menubar
            _("&Add Document to shelf..."),
            # Translators: the help text of an item in the application menubar
            _("Add the current book to the bookshelf"),
        )
        self.Append(
            StatefulBookshelfMenuIds.remove_current_book_from_shelf,
            # Translators: the label of an item in the application menubar
            _("&Remove Document from shelf..."),
            # Translators: the help text of an item in the application menubar
            _("Remove the current book from the bookshelf"),
        )
        self.Append(
            StatelessBookshelfMenuIds.create_new_category,
            # Translators: the label of an item in the application menubar
            _("Create New &Category"),
            # Translators: the help text of an item in the application menubar
            _("Create a new book category in your bookshelf"),
        )

        # Append the menu
        # Translators: the label of an item in the application menubar
        self.view.fileMenu.InsertMenu(7, -1, _("Books&helf"), self, _("Bookshelf options"))

        # EventHandlers
        self.view.Bind(wx.EVT_MENU, self.onOpenBookshelf, id=StatelessBookshelfMenuIds.open_bookshelf)

    def onOpenBookshelf(self, event):
        winsound.Beep(2000, 200)
        raise TypeError("Hi")
        BookshelfWindow(self.view).Show()