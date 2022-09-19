# coding: utf-8

from __future__ import annotations

import operator
import os

import wx
import wx.lib.filebrowsebutton as filebrowse
import wx.lib.sized_controls as sc

from bookworm import speech
from bookworm.gui.components import (ColumnDefn, ImmutableObjectListView,
                                     SimpleDialog, make_sized_static_box)
from bookworm.logger import logger
from bookworm.reader import EBookReader
from bookworm.resources import sounds

from .models import Category, Document, DocumentTag, Page, Tag

log = logger.getChild(__name__)


class EditDocumentClassificationDialog(SimpleDialog):
    def __init__(
        self,
        *args,
        categories: list[str] = None,
        given_category: str = None,
        tags_names: list[str] = (),
        can_fts_index=True,
        **kwargs,
    ):
        self.categories = categories or [cat.name for cat in Category.get_all()]
        self.given_category = given_category
        self.tags_names = tags_names
        self.can_fts_index = can_fts_index
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        parent.SetSizerType("form")
        # Translators: label of a combo box for choosing a document's reading list
        wx.StaticText(parent, -1, _("Reading List"))
        self.categoryCombo = wx.ComboBox(parent, -1, choices=self.categories)
        self.categoryCombo.SetSizerProps(expand=True)
        # Translators: label of a text box for entering a document's collections
        wx.StaticText(parent, -1, _("Collections"))
        self.tagsTextCtrl = wx.TextCtrl(parent, -1, value=" ".join(self.tags_names))
        self.tagsTextCtrl.SetSizerProps(expand=True)
        # Translators: label of a check box
        add_to_fts_label = _("Add to full-text search index")
        if self.can_fts_index:
            self.addToFTSCheckbox = wx.CheckBox(parent, -1, add_to_fts_label)
            self.addToFTSCheckbox.SetValue(True)
        else:
            self.addToFTSCheckbox = wx.CheckBox(
                parent, -1, add_to_fts_label, style=wx.CHK_3STATE
            )
            self.addToFTSCheckbox.Set3StateValue(wx.CHK_UNDETERMINED)
            self.addToFTSCheckbox.Enable(False)
        if self.given_category:
            self.categoryCombo.SetStringSelection(self.given_category)

    def ShowModal(self):
        if (retval := super().ShowModal()) == wx.ID_OK:
            return (
                self.categoryCombo.GetValue().strip(),
                tuple(tg.strip() for tg in self.tagsTextCtrl.GetValue().split(" ")),
                self.addToFTSCheckbox.IsChecked(),
            )


class AddFolderToLocalBookshelfDialog(SimpleDialog):
    def addControls(self, parent):
        parent.SetSizerType("vertical")
        self.folderCtrl = filebrowse.DirBrowseButton(
            parent,
            -1,
            # Translators: label of an edit control for entering the path to a folder to import to the bookshelf
            labelText=_("Select a folder:"),
            # Translators: label of a button
            buttonText=("Browse..."),
            toolTip="",
        )
        # Translators: label of a combo box for choosing a document's reading list
        wx.StaticText(parent, -1, _("Reading List"))
        self.categoryCombo = wx.ComboBox(
            parent, -1, choices=[cat.name for cat in Category.get_all()]
        )
        self.categoryCombo.SetSizerProps(expand=True)
        # Translators: label of a check box
        self.addToFTSCheckbox = wx.CheckBox(
            parent, -1, _("Add to full-text search index")
        )
        self.addToFTSCheckbox.SetValue(True)

    def ShowModal(self):
        if (retval := super().ShowModal()) == wx.ID_OK:
            selected_folder = self.folderCtrl.GetValue()
            if os.path.isdir(selected_folder):
                return (
                    selected_folder,
                    self.categoryCombo.GetValue(),
                    self.addToFTSCheckbox.IsChecked(),
                )


class SearchBookshelfDialog(SimpleDialog):
    def addControls(self, parent):
        parent.SetSizerType("vertical")
        # Translators: label of a text box for entering a search term
        wx.StaticText(parent, -1, _("Search"))
        self.searchQueryTextCtrl = wx.TextCtrl(parent, -1)
        self.searchQueryTextCtrl.SetSizerProps(expand=True)
        # Translators: title of a group of controls to select which document field to search in when searching bookshelf
        searchFieldBox = make_sized_static_box(parent, _("Search Field"))
        pnl = sc.SizedPanel(searchFieldBox, -1)
        pnl.SetSizerType("horizontal")
        # Translators: label of a check box that enables/disables searching document  title when searching the bookshelf
        self.shouldSearchInTitle = wx.CheckBox(pnl, -1, _("Title"))
        # Translators: label of a check box that enables/disables searching document content when searching the bookshelf
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
                self.shouldSearchInContent.IsChecked(),
            )


class BookshelfSearchResultsDialog(SimpleDialog):
    def __init__(
        self, *args, title_search_results=(), content_search_results=(), **kwargs
    ):
        self.title_search_results = title_search_results
        self.content_search_results = content_search_results
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        parent.SetSizerType("vertical")
        self.tabs = wx.Notebook(parent, -1)
        self.tabs.AddPage(
            SearchResultsPage(
                self.tabs,
                self.title_search_results,
                # Translators: label of a list showing search results of documents with title matching the given  search query
                _("Title matches"),
            ),
            # Translators: the label of a tab in a tabl control in a dialog showing a list of search results in the bookshelf
            _("Title Matches"),
        )
        self.tabs.AddPage(
            SearchResultsPage(
                self.tabs,
                self.content_search_results,
                # Translators: label of a list showing search results of content matching the given  search query
                _("Content matches"),
            ),
            # Translators: the label of a tab in a tabl control in a dialog showing a list of search results in the bookshelf
            _("Content Matches"),
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
            ColumnDefn(_("Snippet"), "left", 255, operator.attrgetter("snippet")),
            ColumnDefn(
                # Translators: header of a column in a list control in a dialog showing a list of search results of matching document titles
                _("Title"),
                "center",
                255,
                operator.attrgetter("document_title"),
            ),
            # Translators: header of a column in a list control in a dialog showing a list of search results of matching document pages
            ColumnDefn(_("Page"), "right", 120, lambda ins: ins.page_index + 1),
        )
        wx.StaticText(self, -1, list_label)
        self.result_list = ImmutableObjectListView(self, -1, columns=column_spec)
        self.result_list.set_objects(search_results, set_focus=False)
        self.result_list.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivated, self.result_list
        )

    def onItemActivated(self, event):
        selected_result = self.result_list.get_selected()
        page = selected_result.page_index
        position = Page.get_text_start_position(
            selected_result.page_id, selected_result.snippet
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
            # Translators: title of a list control colum showing errors encountered when bundling documents
            ColumnDefn(_("Error"), "left", 255, operator.itemgetter(0)),
            # Translators: title of a list control colum showing the file names of files not bundled due to errors when bundling documents
            ColumnDefn(_("File Name"), "center", 255, operator.itemgetter(1)),
            # Translators: title of a list control colum showing the document titles  of documents not bundled due to errors when bundling documents
            ColumnDefn(_("Title"), "right", 255, operator.itemgetter(2)),
        )
        # Translators: label of a list control showing file copy errors
        wx.StaticText(parent, -1, _("Errors"))
        result_list = ImmutableObjectListView(parent, -1, columns=column_spec)
        # Translators: label shown in a list control indicating the failure to copy the document when bundling documents
        reason = _("Failed to copy document")
        result_list.set_objects([(reason, *i) for i in self.info], set_focus=True)

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of the cancel button in a dialog
        cancelBtn = wx.Button(self, wx.ID_CANCEL, _("&Close"))
        btnsizer.AddButton(cancelBtn)
        btnsizer.Realize()
        return btnsizer
