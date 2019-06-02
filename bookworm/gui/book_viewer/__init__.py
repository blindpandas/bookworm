from weakref import ref
import wx
from wx.adv import Sound
from bookworm.logger import logger
from bookworm.paths import app_path
from bookworm.ebook_reader import EBookReader
from bookworm.decorators import only_when_reader_ready, only_if_pagination_is_supported
from .viewer_menubar import ViewerWindowMenubarMixin


log = logger.getChild(__name__)




class BookViewerWindow(wx.Frame, ViewerWindowMenubarMixin):
    """The book viewer window."""

    _sound_files = dict(
        pagination=app_path("sounds", "pagination.wav")
    )

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title)

        self.createMenuBar()
        self.CreateStatusBar()

        # Now create the Panel to put the other controls on.
        panel = wx.Panel(self, size=(1000, 600))

        # Create the book reader controls
        tocTreeLabel = wx.StaticText(panel, -1, "Table of content")
        self.tocTreeCtrl = wx.TreeCtrl(panel,
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
        lftSizer.Add(self.tocTreeCtrl, 1)
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
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onTocTreeChangeSelection, self.tocTreeCtrl)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onTOCItemClick, self.tocTreeCtrl)
        self.contentTextCtrl.Bind(wx.EVT_KEY_UP, self.onContentCtrlTextKeyUp, self.contentTextCtrl)

        # Instantiate the reader 
        self.reader = EBookReader(self)
        # Load some sound files
        self._pagination_sound = Sound(self._sound_files["pagination"])

    def setContent(self, content):
        self.contentTextCtrl.Clear()
        self.contentTextCtrl.WriteText(content)
        self.contentTextCtrl.SetInsertionPoint(0)
        if not self.contentTextCtrl.HasFocus():
            wx.CallAfter(self.contentTextCtrl.SetFocus)

    @only_when_reader_ready
    def onTocTreeChangeSelection(self, event):
        selectedItem = event.GetItem()
        self.SetStatusText(self.tocTreeCtrl.GetItemText(selectedItem))

    @only_when_reader_ready
    def onTOCItemClick(self, event):
        selectedItem = event.GetItem()
        current_item = self.tocTreeCtrl.GetItemData(selectedItem)
        content = self.reader.get_item_content(item=current_item)
        self.setContent(content)
        self.reader.active_item = current_item

    @only_when_reader_ready
    @only_if_pagination_is_supported
    def onContentCtrlTextKeyUp(self, event):
        if not all((self.reader.supports_pagination, self.reader.ready)):
            return event.Skip()
        key_code = event.GetKeyCode()
        content = None
        if key_code == wx.WXK_RETURN:
            content = self.reader.navigate(to="next")
        elif key_code == wx.WXK_BACK:
            content = self.reader.navigate(to="prev")
        if content is not None:
            self.setContent(content)
            self._pagination_sound.Play()
            event.Skip(False)

    def addTocTree(self, toc):
        self.tocTreeCtrl.DeleteAllItems()
        root_item = toc[0]
        root = self.tocTreeCtrl.AddRoot(root_item.title, data=root_item)
        self._populate_tree(toc[1:], root=root)
        root_item.data["tree_id"] = ref(root)
        self.reader.active_item = root_item

    def tocTreeSetSelection(self, item):
        tree_id = item.data.get("tree_id", lambda: None).__call__()
        if tree_id is not None:
            self.tocTreeCtrl.SelectItem(tree_id)
            self.tocTreeCtrl.SetFocusedItem(tree_id)

    def _populate_tree(self, toc, root):
        for item in toc:
            entry = self.tocTreeCtrl.AppendItem(root, item.title, data=item)
            item.data["tree_id"] = ref(entry)
            if item.children:
                self._populate_tree(item.children, entry)

    def getBookInfoText(self):
        info = self.reader.current_book
        return "\r\n".join([
            f"Book Title: {info.title}",
            f"Author: {info.author}",
            f"Publisher: {info.publisher}",
            f"Publication Year: {info.publication_year}"
        ])
        
