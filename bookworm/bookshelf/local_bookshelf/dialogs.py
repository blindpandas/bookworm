# coding: utf-8

from __future__ import annotations
import os
import operator
import wx
import wx.lib.sized_controls as sc
import wx.lib.filebrowsebutton as filebrowse
from bookworm import speech
from bookworm.reader import EBookReader
from bookworm.resources import sounds
from bookworm.gui.components import (
    SimpleDialog,
    ColumnDefn,
    ImmutableObjectListView,
    make_sized_static_box
)
from bookworm.logger import logger
from .models import (
    Document,
    Page,
    Category,
    Tag,
    DocumentTag
)


log = logger.getChild(__name__)



class EditDocumentClassificationDialog(SimpleDialog):

    def __init__(self, *args, categories: list[str]=None, given_category: str=None, tags_names: list[str]=(), **kwargs):
        self.categories = categories or [cat.name for cat in Category.get_all()]
        self.given_category = given_category
        self.tags_names = tags_names
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        parent.SetSizerType('form')
        wx.StaticText(parent, -1, _("Reading List"))
        self.categoryCombo = wx.ComboBox(
            parent,
            -1,
            choices=self.categories
        )
        self.categoryCombo.SetSizerProps(expand=True)
        wx.StaticText(parent, -1, _("Collections"))
        self.tagsTextCtrl = wx.TextCtrl(
            parent,
            -1,
            value=" ".join(self.tags_names)
        )
        self.tagsTextCtrl.SetSizerProps(expand=True)
        if self.given_category:
            self.categoryCombo.SetStringSelection(self.given_category)

    def ShowModal(self):
        if (retval := super().ShowModal()) == wx.ID_OK:
            return (
                self.categoryCombo.GetValue().strip(),
                tuple(tg.strip() for tg in self.tagsTextCtrl.GetValue().split(" "))
            )



class AddFolderToLocalBookshelfDialog(SimpleDialog):

    def addControls(self, parent):
        parent.SetSizerType('vertical')
        self.folderCtrl = filebrowse.DirBrowseButton(
            parent,
            -1,
            # Translators: label of an edit control
            labelText=_("Select a folder:"),
            # Translators: label of a button
            buttonText=("Browse..."),
            toolTip='',
        )
        wx.StaticText(parent, -1, _("Reading List"))
        self.categoryCombo = wx.ComboBox(
            parent,
            -1,
            choices=[cat.name for cat in Category.get_all()]
        )
        self.categoryCombo.SetSizerProps(expand=True)

    def ShowModal(self):
        if (retval := super().ShowModal()) == wx.ID_OK:
            selected_folder = self.folderCtrl.GetValue()
            if os.path.isdir(selected_folder):
                return (selected_folder,  self.categoryCombo.GetValue())


class SearchBookshelfDialog(SimpleDialog):

    def addControls(self, parent):
        parent.SetSizerType('vertical')
        wx.StaticText(parent, -1, _("Search"))
        self.searchQueryTextCtrl = wx.TextCtrl(parent, -1)
        self.searchQueryTextCtrl.SetSizerProps(expand=True)
        searchFieldBox = make_sized_static_box(parent, _("Search Field"))
        pnl = sc.SizedPanel(searchFieldBox, -1)
        pnl.SetSizerType('horizontal')
        self.shouldSearchInTitle = wx.CheckBox(pnl, -1, _("Title"))
        self.shouldSearchInContent = wx.CheckBox(pnl, -1, _("Content"))
        self.shouldSearchInTitle.SetValue(True)
        self.shouldSearchInContent.SetValue(True)

    def ShowModal(self):
        if (retval := super().ShowModal()) == wx.ID_OK:
            search_query = self.searchQueryTextCtrl.GetValue()
            if not search_query.strip():
                return
            return (
                search_query,
                self.shouldSearchInTitle.IsChecked(),
                self.shouldSearchInContent.IsChecked()
            )


class BookshelfSearchResultsDialog(SimpleDialog):

    def __init__(self, *args, title_search_results=(), content_search_results=(), **kwargs):
        self.title_search_results = title_search_results
        self.content_search_results = content_search_results
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        parent.SetSizerType('vertical')
        self.tabs = wx.Notebook(parent, -1)
        self.tabs.AddPage(
            SearchResultsPage(self.tabs, self.title_search_results, _("Title Matches")),
            _("Title Matches")
        )
        self.tabs.AddPage(
            SearchResultsPage(self.tabs, self.content_search_results, _("Content Matches")),
            _("Content Matches")
        )

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of the cancel button in a dialog
        cancelBtn = wx.Button(self, wx.ID_CANCEL, _("&Close"))
        btnsizer.AddButton(cancelBtn)
        btnsizer.Realize()
        return btnsizer



class SearchResultsPage(sc.SizedPanel):

    def __init__(self, parent, search_results, list_label):
        super().__init__(parent, -1)
        column_spec = (
            ColumnDefn(_("Snippet"), 'left', 255, operator.attrgetter('snippet')),
            ColumnDefn(_("Title"), 'center', 255, operator.attrgetter('document_title')),
            ColumnDefn(_("Page"), 'right', 120, lambda ins: ins.page_index + 1),
        )
        wx.StaticText(self, -1, list_label)
        self.result_list = ImmutableObjectListView(self, -1, columns=column_spec)
        self.result_list.set_objects(search_results, set_focus=False)
        self.result_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivated, self.result_list)

    def onItemActivated(self, event):
        selected_result = self.result_list.get_selected()
        page = selected_result.page_index
        position = Page.get_text_start_position(
            selected_result.page_id,
            selected_result.snippet
        )
        uri = selected_result.document.uri.create_copy(
            openner_args=dict(page=page, position=position)
        )
        # Translators: spoken message
        speech.announce("Openning document...")
        sounds.navigation.play()
        EBookReader.open_document_in_a_new_instance(uri)



class BundleErrorsDialog(SimpleDialog):

    def __init__(self, *args, info: list[tuple[str]], **kwargs):
        self.info = info
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        parent.SetSizerType("vertical")
        column_spec = (
            # Translators: title of a list control colum
            ColumnDefn(_("Error"), 'left', 255, operator.itemgetter(0)),
            # Translators: title of a list control colum
            ColumnDefn(_("File Name"), 'center', 255, operator.itemgetter(1)),
            # Translators: title of a list control colum
            ColumnDefn(_("Title"), 'right', 255, operator.itemgetter(2)),
        )
        # Translators: label of a list control showing file copy errors
        wx.StaticText(parent, -1, _("Errors"))
        result_list = ImmutableObjectListView(parent, -1, columns=column_spec)
        reason = _("Failed to copy document")
        result_list.set_objects([(reason, *i) for i in self.info], set_focus=True)

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of the cancel button in a dialog
        cancelBtn = wx.Button(self, wx.ID_CANCEL, _("&Close"))
        btnsizer.AddButton(cancelBtn)
        btnsizer.Realize()
        return btnsizer


