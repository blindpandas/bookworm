# coding: utf-8

import threading
import wx
import wx.lib.sized_controls as sc
from itertools import chain
from bookworm import config
from bookworm.document_formats import SearchRequest
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from bookworm.gui.components import (
    Dialog,
    SimpleDialog,
    DialogListCtrl,
    EnhancedSpinCtrl,
    PageRangeControl,
    make_sized_static_box,
)
from .navigation import NavigationProvider


log = logger.getChild(__name__)


class SearchResultsDialog(Dialog):
    """Search Results."""

    def __init__(self, highlight_func, num_pages, *args, **kwargs):
        self.highlight_func = highlight_func
        self.num_pages = num_pages
        self.list_lock = threading.RLock()
        super().__init__(*args, **kwargs)

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
        if self.reader.document.has_toc_tree():
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
        sizer.Add(self.searchResultsListCtrl, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(pbarlabel, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(self.progressbar, 0, wx.EXPAND | wx.ALL, 10)
        self.progressbar.SetRange(self.num_pages)
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
            page = (
                self.searchResultsListCtrl.GetItemText(idx)
                if not self.reader.document.is_single_page_document()
                else 1
            )
            pos = self.searchResultsListCtrl.GetItemData(idx)
            self.Close()
            self.Destroy()
            self.highlight_func(int(page) - 1, pos)
            self.parent._last_search_index = idx

    def addResultSet(self, resultset):
        for result in resultset:
            self.addResult(result)
        wx.CallAfter(self.progressbar.SetValue, self.progressbar.GetValue() + 1)

    def addResult(self, result):
        if not self.IsShown():
            return
        with self.list_lock:
            self.addResultToList(result)

    def addResultToList(self, result):
        count = self.searchResultsListCtrl.ItemCount
        page_display_text = (
            str(result.page + 1) if not self.reader.document.is_single_page_document() else ""
        )
        index = self.searchResultsListCtrl.InsertItem(count, page_display_text)
        self.searchResultsListCtrl.SetItem(index, 1, result.excerpt)
        if self.reader.document.has_toc_tree():
            self.searchResultsListCtrl.SetItem(index, 2, result.section)
        self.searchResultsListCtrl.SetItemData(index, result.position)


class SearchBookDialog(SimpleDialog):
    """Full text search dialog."""

    def addControls(self, parent):
        self.reader = self.parent.reader
        num_pages = len(self.parent.reader.document)
        recent_terms = config.conf["history"]["recent_terms"]

        # Translators: the label of an edit field in the search dialog
        wx.StaticText(parent, -1, _("Search term:"))
        self.searchTermTextCtrl = wx.ComboBox(
            parent, -1, choices=recent_terms, style=wx.CB_DROPDOWN
        )
        self.searchTermTextCtrl.SetSizerProps(expand=True)
        # Translators: the label of a checkbox
        self.isCaseSensitive = wx.CheckBox(parent, -1, _("Case sensitive"))
        # Translators: the label of a checkbox
        self.isWholeWord = wx.CheckBox(parent, -1, _("Match whole word only"))
        # Translators: the label of a checkbox
        self.isRegex = wx.CheckBox(parent, -1, _("Regular expression"))
        self.pageRange = PageRangeControl(parent, self.reader.document)
        self.Bind(wx.EVT_CHECKBOX, self.onIsRegex, self.isRegex)
        self.Bind(wx.EVT_BUTTON, self.onCloseDialog, id=wx.ID_CANCEL)

    def GetValue(self):
        from_page, to_page = self.pageRange.get_range()
        return SearchRequest(
            term=self.searchTermTextCtrl.GetValue().strip(),
            is_regex=self.isRegex.IsChecked(),
            case_sensitive=self.isCaseSensitive.IsChecked(),
            whole_word=self.isWholeWord.IsChecked(),
            from_page=from_page,
            to_page=to_page,
        )

    def onIsRegex(self, event):
        controlledItems = (self.isWholeWord,)
        enable = not event.IsChecked()
        for ctrl in controlledItems:
            ctrl.SetValue(False)
            ctrl.Enable(enable)

    def onSearchRange(self, event):
        radio = event.GetEventObject()
        if radio == self.hasPage:
            controls = self.page_controls
        else:
            controls = self.sect_controls
        for ctrl in chain(self.page_controls, self.sect_controls):
            ctrl.Enable(ctrl in controls)

    def onCloseDialog(self, event):
        if self.pageRange.ShouldCloseParentDialog():
            event.Skip()


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
