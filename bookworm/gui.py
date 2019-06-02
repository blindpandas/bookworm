import sys
import os
import enum
import wx
from wx.adv import Sound
from pathlib import Path
from .logger import logger
from .paths import app_path
from .controller import EBookController


log = logger.getChild(__name__)


class MenuIds(enum.IntEnum):
    open = 210
    goToPage = 220


class MainFrame(wx.Frame):
    """
    """

    _sound_files = dict(
        pagination=app_path("sounds", "pagination.wav")
    )

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title)

        # Create the menubar
        menuBar = wx.MenuBar()

        # and a menu
        fileMenu = wx.Menu()
        navigationMenu = wx.Menu()

        # add items to the menu,
        fileMenu.Append(MenuIds.open, "&Open\tCtrl-O", "Open a book")
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit this simple sample")
        navigationMenu.Append(MenuIds.goToPage, "&Go To Page...\tCtrl-g", "Go to page")

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.onOpenEBook, id=MenuIds.open)
        self.Bind(wx.EVT_MENU, self.onClose, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.onGoToPage, id=MenuIds.goToPage)

        # and put the menu on the menubar
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(navigationMenu, "&Navigation")
        self.SetMenuBar(menuBar)

        self.CreateStatusBar()

        # Now create the Panel to put the other controls on.
        panel = wx.Panel(self, size=(1000, 600))

        # Create the book reader controls
        tocTreeLabel = wx.StaticText(panel, -1, "Table of content")
        self.tocTree = wx.TreeCtrl(panel,
            size=(280, 160),
            style=wx.TR_TWIST_BUTTONS|wx.TR_NO_LINES|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_ROW_LINES,
            name="tbl_of_content"
        )
        contentTextCtrlLabel = wx.StaticText(panel, -1, "Content")
        self.contentTextCtrl = wx.TextCtrl(panel,
            size=(200, 160),
            style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_PROCESS_ENTER|wx.TE_RICH2|wx.TE_AUTO_URL|wx.TE_NOHIDESEL
        )

        # Use a sizer to layout the controls, stacked horizontally and with
        # a 10 pixel border around each
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        lftSizer = wx.BoxSizer(wx.VERTICAL)
        rgtSizer = wx.BoxSizer(wx.VERTICAL)
        lftSizer.Add(tocTreeLabel, 0)
        lftSizer.Add(self.tocTree, 1)
        rgtSizer.Add(contentTextCtrlLabel, 0)
        rgtSizer.Add(self.contentTextCtrl, 1, wx.EXPAND)
        mainSizer.Add(lftSizer, 0, wx.ALL | wx.EXPAND, 10)
        mainSizer.Add(rgtSizer, 1, wx.ALL | wx.EXPAND, 10)
        panel.SetSizer(mainSizer)
        panel.Layout()

        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer()
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        self.CenterOnScreen(wx.BOTH)
        
        # Bind Events
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onTocTreeChangeSelection, self.tocTree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onTOCItemClick, self.tocTree)
        self.contentTextCtrl.Bind(wx.EVT_KEY_UP, self.onContentCtrlTextKeyUp, self.contentTextCtrl)

        # Instantiate the controller 
        self.controller = EBookController(self)
        # Load some sound files
        self._pagination_sound = Sound(self._sound_files["pagination"])

    def setContent(self, content):
        self.contentTextCtrl.Clear()
        self.contentTextCtrl.WriteText(content)
        self.contentTextCtrl.SetInsertionPoint(0)
        if not self.contentTextCtrl.HasFocus():
            wx.CallAfter(self.contentTextCtrl.SetFocus)

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
            self.controller.open_ebook(file, format=os.path.splitext(file)[-1].lstrip("."))
        openFileDlg.Destroy()
        self.setContent("")
        wx.CallAfter(self.tocTree.SetFocus)

    def onClose(self, evt):
        self.Close()
        wx.GetApp().ExitMainLoop()
        sys.exit(0)

    def onGoToPage(self, event):
        prev_entry = getattr(self, "_go_to_prev_entry", None)
        page_number = None
        root = self.tocTree.GetRootItem()
        dlg = wx.TextEntryDialog(self,
            f"Enter the page number 1 to {len(self.controller.reader)}:",
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
                rootItem = self.tocTree.GetItemData(root)
                if (page_number <= 0) or (page_number > rootItem.data["paginater"].last):
                    wx.MessageBox(
                      f"There is no page numbered {page_number} in this document.",
                      caption="Invalid Page Number",
                      style=wx.OK|wx.ICON_EXCLAMATION,
                      parent=self
                    )
                    self._go_to_prev_entry = None
                    return self.onGoToPage(event)
                self.setContent(self.controller.get_page_content(page_number - 1))
                self._go_to_prev_entry = value
                self.tocTree.SelectItem(root)
                self.tocTree.SetFocusedItem(root)

    def onTocTreeChangeSelection(self, event):
        selectedItem = event.GetItem()
        self.SetStatusText(self.tocTree.GetItemText(selectedItem))

    def onTOCItemClick(self, event):
        selectedItem = event.GetItem()
        current_item = self.tocTree.GetItemData(selectedItem)
        content = self.controller.get_item_content(item=current_item)
        self.setContent(content)
        self.controller.set_active_item(current_item)

    def onContentCtrlTextKeyUp(self, event):
        if not all((self.controller.supports_pagination, self.controller.ready)):
            return event.Skip()
        key_code = event.GetKeyCode()
        content = None
        if key_code == wx.WXK_RETURN:
            content = self.controller.navigate(to="next")
        elif key_code == wx.WXK_BACK:
            content = self.controller.navigate(to="prev")
        if content is not None:
            self.setContent(content)
            self._pagination_sound.Play()
            event.Skip(False)

    def add_toc_tree(self, toc):
        self.tocTree.DeleteAllItems()
        root_item = toc.pop(0)
        root = self.tocTree.AddRoot(root_item.title, data=root_item)
        self._populate_tree(toc, root=root)
        self.controller.set_active_item(root_item)

    def _populate_tree(self, toc, root):
        for item in toc:
            entry = self.tocTree.AppendItem(root, item.title, data=item)
            if item.children:
                self._populate_tree(item.children, entry)

    def _get_ebooks_wildcards(self):
        rv = []
        for cls in self.controller.reader_classes:
            for ext in cls.extensions:
                rv.append(f"{cls.name} ({ext})|{ext}|")
        rv[-1] = rv[-1].rstrip("|")
        return "".join(rv)

    def getBookInfoText(self):
        info = self.controller.current_book
        return "\r\n".join([
            f"Book Title: {info.title}",
            f"Author: {info.author}",
            f"Publisher: {info.publisher}",
            f"Publication Year: {info.publication_year}"
        ])
        

class BookReaderApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, "Bookworm")
        self.SetTopWindow(frame)

        frame.Show(True)
        return True
