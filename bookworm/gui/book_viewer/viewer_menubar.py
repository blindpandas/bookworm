import sys
from pathlib import Path
import enum
import wx
from bookworm.logger import logger
from bookworm.decorators import only_when_reader_ready, only_if_pagination_is_supported


log = logger.getChild(__name__)



class MenuIds(enum.IntEnum):
    open = 210
    goToPage = 220


class ViewerWindowMenubarMixin:

    def createMenuBar(self):
        # Create the menubar
        menuBar = wx.MenuBar()

        # and a menu
        fileMenu = wx.Menu()
        navigationMenu = wx.Menu()

        # add items to the menu,
        fileMenu.Append(MenuIds.open, "&Open\tCtrl-O", "Open a book")
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit book viewer")
        navigationMenu.Append(MenuIds.goToPage, "&Go To Page...\tCtrl-g", "Go to page")

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.onOpenEBook, id=MenuIds.open)
        self.Bind(wx.EVT_MENU, self.onClose, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.onGoToPage, id=MenuIds.goToPage)

        # and put the menu on the menubar
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(navigationMenu, "&Navigation")
        self.SetMenuBar(menuBar)

    def onOpenEBook(self, event):
        openFileDlg = wx.FileDialog(
            self,
            message="Choose an e-book",
            defaultDir=str(Path.home()),
            defaultFile="",
            wildcard=self._get_ebooks_wildcards(),
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST,
        )
        if openFileDlg.ShowModal() == wx.ID_OK:
            file = openFileDlg.GetPath()
            self.reader.load(file)
        openFileDlg.Destroy()
        self.setContent("")
        wx.CallAfter(self.tocTreeCtrl.SetFocus)

    def onClose(self, evt):
        self.reader.unload()
        self.Close()
        wx.GetApp().ExitMainLoop()
        sys.exit(0)

    @only_when_reader_ready
    @only_if_pagination_is_supported
    def onGoToPage(self, event):
        prev_entry = getattr(self, "_go_to_prev_entry", None)
        page_number = None
        root = self.tocTreeCtrl.GetRootItem()
        dlg = wx.TextEntryDialog(self,
            f"Enter the page number 1 to {len(self.reader.reader)}:",
            "Go To Page"
        )
        if prev_entry is not None:
            dlg.SetValue(prev_entry)
        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.GetValue()
            try:
                page_number = int(value)
            except ValueError:
                log.debug(f"Not a valid number `{value}`.")
                return
            finally:
                dlg.Destroy()
            if page_number is not None:
                rootItem = self.tocTreeCtrl.GetItemData(root)
                if (page_number <= 0) or (page_number > rootItem.pager.last):
                    wx.MessageBox(
                      f"There is no page numbered {page_number} in this document.",
                      caption="Invalid Page Number",
                      style=wx.OK|wx.ICON_EXCLAMATION,
                      parent=self
                    )
                    self._go_to_prev_entry = None
                    return self.onGoToPage(event)
                self.setContent(self.reader.get_page_content(page_number - 1))
                self._go_to_prev_entry = value
                self.tocTreeSetSelection(root)

    def _get_ebooks_wildcards(self):
        rv = []
        for cls in self.reader.document_classes:
            for ext in cls.extensions:
                rv.append(f"{cls.name} ({ext})|{ext}|")
        rv[-1] = rv[-1].rstrip("|")
        return "".join(rv)
