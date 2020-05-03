# coding: utf-8

import wx
import wx.lib.scrolledpanel as scrolled
import fitz
from itertools import chain
from bookworm import config
from bookworm import speech
from bookworm.document_formats import SearchRequest
from bookworm.signals import reader_page_changed
from bookworm.utils import gui_thread_safe
from bookworm.runtime import IS_HIGH_CONTRAST_ACTIVE
from bookworm.logger import logger
from bookworm.gui.components import Dialog, SimpleDialog, DialogListCtrl, EnhancedSpinCtrl
from .navigation import NavigationProvider


log = logger.getChild(__name__)


class SearchResultsDialog(Dialog):
    """Search Results."""

    def addControls(self, sizer, parent):
        self.reader = self.parent.reader
        # Translators: the label of a list of search results
        label = wx.StaticText(parent, -1, _("Search Results"))
        self.searchResultsListCtrl = DialogListCtrl(parent, -1)
        self.searchResultsListCtrl.AppendColumn(
            # Translators: the title of a column in the search results list
            _("Page"),
            format=wx.LIST_FORMAT_LEFT,
            width=20,
        )
        self.searchResultsListCtrl.AppendColumn(
            # Translators: the title of a column in the search results list showing
            # an excerpt of the text of the search result
            _("Text"),
            format=wx.LIST_FORMAT_CENTER,
            width=50,
        )
        self.searchResultsListCtrl.AppendColumn(
            # Translators: the title of a column in the search results list
            # showing the title of the chapter in which this occurrence was found
            _("Section"),
            format=wx.LIST_FORMAT_LEFT,
            width=30,
        )
        self.searchResultsListCtrl.SetColumnWidth(0, 100)
        self.searchResultsListCtrl.SetColumnWidth(1, 100)
        self.searchResultsListCtrl.SetColumnWidth(2, 100)
        # Translators: the label of a progress bar indicating the progress of the search process
        pbarlabel = wx.StaticText(parent, -1, _("Search Progress:"))
        self.progressbar = wx.Gauge(parent, -1, style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 10)
        sizer.Add(
            self.searchResultsListCtrl, 1, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, 10
        )
        sizer.Add(pbarlabel, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(self.progressbar, 0, wx.EXPAND | wx.ALL, 10)
        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self.onItemClick, self.searchResultsListCtrl
        )

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button to close the dialog
        btnsizer.AddButton(wx.Button(parent, wx.ID_CANCEL, "&Close"))
        btnsizer.Realize()
        return btnsizer

    def onItemClick(self, event):
        idx = self.searchResultsListCtrl.GetFocusedItem()
        if idx != wx.NOT_FOUND:
            page = self.searchResultsListCtrl.GetItemText(idx)
            pos = self.searchResultsListCtrl.GetItemData(idx)
            self.Close()
            self.Destroy()
            self.parent.highlight_search_result(int(page) - 1, pos)
            self.parent._last_search_index = idx

    def addResult(self, page, snip, section, pos):
        count = self.searchResultsListCtrl.ItemCount
        index = self.searchResultsListCtrl.InsertItem(count, str(page + 1))
        self.searchResultsListCtrl.SetItem(index, 1, snip)
        self.searchResultsListCtrl.SetItem(index, 2, section)
        self.searchResultsListCtrl.SetItemData(index, pos)


class SearchBookDialog(Dialog):
    """Full text search dialog."""

    def addControls(self, sizer, parent):
        self.reader = self.parent.reader
        num_pages = len(self.parent.reader.document)
        recent_terms = config.conf["history"]["recent_terms"]
        # Translators: the label of an edit field in the search dialog
        st_label = wx.StaticText(parent, -1, _("Search term:"))
        self.searchTermTextCtrl = wx.ComboBox(
            parent, -1, choices=recent_terms, style=wx.CB_DROPDOWN
        )
        # Translators: the label of a checkbox
        self.isCaseSensitive = wx.CheckBox(parent, -1, _("Case sensitive"))
        # Translators: the label of a checkbox
        self.isWholeWord = wx.CheckBox(parent, -1, _("Match whole word only"))
        # Translators: the title of a group of controls in the search dialog
        rbTitle = wx.StaticBox(parent, -1, _("Search Range"))
        searchRangeBox = wx.StaticBoxSizer(rbTitle, wx.VERTICAL)
        # Translators: the label of a radio button in the search dialog
        self.hasPage = wx.RadioButton(parent, -1, _("Page Range"), style=wx.RB_GROUP)
        rsizer = wx.BoxSizer(wx.HORIZONTAL)
        # Translators: the label of an edit field in the search dialog
        # to enter the page from which the search will start
        fpage_label = wx.StaticText(parent, -1, _("From:"))
        self.fromPage = EnhancedSpinCtrl(parent, -1, min=1, max=num_pages, value="1")
        # Translators: the label of an edit field in the search dialog
        # to enter the page number at which the search will stop
        tpage_label = wx.StaticText(parent, -1, _("To:"))
        self.toPage = EnhancedSpinCtrl(
            parent, -1, min=1, max=num_pages, value=str(num_pages)
        )
        rsizer.AddMany(
            [
                (fpage_label, 0, wx.ALL, 5),
                (self.fromPage, 1, wx.ALL, 5),
                (tpage_label, 0, wx.ALL, 5),
                (self.toPage, 1, wx.ALL, 5),
            ]
        )
        # Translators: the label of a radio button in the search dialog
        self.hasSection = wx.RadioButton(parent, -1, _("Specific section"))
        # Translators: the label of a combobox in the search dialog
        # to choose the section to which the search will be confined
        sec_label = wx.StaticText(parent, -1, _("Select section:"))
        self.sectionChoice = wx.Choice(
            parent, -1, choices=[sect.title for sect in self.reader.document.toc_tree]
        )
        secsizer = wx.BoxSizer(wx.HORIZONTAL)
        secsizer.AddMany(
            [(sec_label, 0, wx.ALL, 5), (self.sectionChoice, 1, wx.ALL, 5)]
        )
        searchRangeBox.Add(self.hasPage, 0, wx.ALL, 10)
        searchRangeBox.Add(rsizer, wx.EXPAND | wx.ALL, 10)
        searchRangeBox.Add(self.hasSection, 0, wx.ALL, 10)
        searchRangeBox.Add(secsizer, wx.EXPAND | wx.ALL, 10)
        sizer.Add(st_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer.Add(self.searchTermTextCtrl, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.isCaseSensitive, 0, wx.TOP | wx.BOTTOM, 10)
        sizer.Add(self.isWholeWord, 0, wx.BOTTOM, 10)
        sizer.Add(searchRangeBox, 0, wx.ALL, 10)
        self.page_controls = (fpage_label, tpage_label, self.fromPage, self.toPage)
        self.sect_controls = (sec_label, self.sectionChoice)
        for ctrl in chain(self.page_controls, self.sect_controls):
            ctrl.Enable(False)
        for radio in (self.hasPage, self.hasSection):
            radio.SetValue(0)
            self.Bind(wx.EVT_RADIOBUTTON, self.onSearchRange, radio)

    def GetValue(self):
        if self.hasSection.GetValue():
            selected_section = self.sectionChoice.GetSelection()
            if selected_section != wx.NOT_FOUND:
                pager = self.reader.document.toc_tree[selected_section].pager
                from_page = pager.first
                to_page = pager.last
        else:
            from_page = self.fromPage.GetValue() - 1
            to_page = self.toPage.GetValue() - 1
        return SearchRequest(
            term=self.searchTermTextCtrl.GetValue().strip(),
            case_sensitive=self.isCaseSensitive.IsChecked(),
            whole_word=self.isWholeWord.IsChecked(),
            from_page=from_page,
            to_page=to_page,
        )

    def onSearchRange(self, event):
        radio = event.GetEventObject()
        if radio == self.hasPage:
            controls = self.page_controls
        else:
            controls = self.sect_controls
        for ctrl in chain(self.page_controls, self.sect_controls):
            ctrl.Enable(ctrl in controls)


class GoToPageDialog(SimpleDialog):
    """Go to page dialog."""

    def addControls(self, parent):
        page_count = len(self.parent.reader.document)
        # Translators: the label of an edit field in the go to page dialog
        label = wx.StaticText(
            parent, -1, _("Page number, of {total}:").format(total=page_count)
        )
        self.pageNumberCtrl = EnhancedSpinCtrl(
            parent,
            -1,
            min=1,
            max=page_count,
            value=str(self.parent.reader.current_page + 1),
        )
        self.pageNumberCtrl.SetSizerProps(expand=True)

    def GetValue(self):
        return self.pageNumberCtrl.GetValue() - 1


class ViewPageAsImageDialog(wx.Dialog):
    """Show the page rendered as an image."""

    def __init__(self, parent, title, size=(450, 450), style=wx.DEFAULT_DIALOG_STYLE):
        super().__init__(parent, title=title, style=style)
        self.parent = parent
        self.reader = self.parent.reader
        # Zoom support
        self.scaling_factor = 0.2
        self._zoom_factor = 1
        self.scroll_rate = 30
        # Translators: the label of the image of a page in a dialog to render the current page
        panel = self.scroll = scrolled.ScrolledPanel(self, -1, name=_("Page"))
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.imageCtrl = wx.StaticBitmap(panel)
        sizer.Add(self.imageCtrl, 1, wx.CENTER | wx.BOTH)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        panel.Layout()
        self.setDialogImage()
        NavigationProvider(
            ctrl=panel,
            reader=self.reader,
            callback_func=self.setDialogImage,
            zoom_callback=self.set_zoom,
        )
        panel.Bind(wx.EVT_KEY_UP, self.onKeyUp, panel)
        panel.SetupScrolling(rate_x=self.scroll_rate, rate_y=self.scroll_rate)
        self._currently_rendered_page = self.reader.current_page
        reader_page_changed.connect(self.onPageChange, sender=self.reader)

    @gui_thread_safe
    def onPageChange(self, sender, current, prev):
        if self._currently_rendered_page != current:
            self.setDialogImage()

    def set_zoom(self, val):
        if val == 0:
            self.zoom_factor = 1
        else:
            self.zoom_factor += val * self.scaling_factor

    @property
    def zoom_factor(self):
        return self._zoom_factor

    @zoom_factor.setter
    def zoom_factor(self, value):
        if (value < 1.0) or (value > 10.0):
            return
        self._zoom_factor = value
        self.setDialogImage(reset_scroll_pos=False)
        self.scroll.SetupScrolling(
            rate_x=self.scroll_rate, rate_y=self.scroll_rate, scrollToTop=False
        )
        # Translators: a message announced to the user when the zoom factor changes
        speech.announce(
            _("Zoom is at {factor} percent").format(factor=int(value * 100))
        )

    def setDialogImage(self, reset_scroll_pos=True):
        bmp, size = self.getPageImage()
        self.imageCtrl.SetSize(size)
        self.imageCtrl.SetBitmap(bmp)
        self._currently_rendered_page = self.reader.current_page
        if reset_scroll_pos:
            self.scroll.SetupScrolling(
                rate_x=self.scroll_rate, rate_y=self.scroll_rate, scrollToTop=False
            )
            wx.CallLater(50, self.scroll.Scroll, 0, 0)

    def getPageImage(self):
        page = self.reader.document[self.reader.current_page]
        mat = fitz.Matrix(self._zoom_factor, self._zoom_factor)
        pix = page.getPixmap(matrix=mat, alpha=True)
        if IS_HIGH_CONTRAST_ACTIVE:
            pix.invertIRect(pix.irect)
        bmp = wx.Bitmap.FromBufferRGBA(pix.width, pix.height, pix.samples)
        size = (bmp.GetWidth(), bmp.GetHeight())
        return bmp, size

    def onKeyUp(self, event):
        event.Skip()
        code = event.GetKeyCode()
        if code == wx.WXK_ESCAPE:
            self.Close()
            self.Destroy()

    def Close(self, *args, **kwargs):
        super().Close(*args, **kwargs)
        reader_page_changed.disconnect(self.onPageChange, sender=self.reader)

