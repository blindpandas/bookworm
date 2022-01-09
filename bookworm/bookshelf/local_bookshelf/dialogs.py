# coding: utf-8

from __future__ import annotations
import os
import wx
import wx.lib.filebrowsebutton as filebrowse

from bookworm.gui.components import SimpleDialog
from bookworm.logger import logger
from .models import Document, Category, Tag, DocumentTag


log = logger.getChild(__name__)



class EditDocumentClassificationDialog(SimpleDialog):

    def __init__(self, *args, categories: list[str]=None, given_category: str=None, tags_names: list[str]=(), **kwargs):
        self.categories = categories or [cat.name for cat in Category.get_all()]
        self.given_category = given_category
        self.tags_names = tags_names
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        parent.SetSizerType('form')
        wx.StaticText(parent, -1, _("Category"))
        self.categoryCombo = wx.ComboBox(
            parent,
            -1,
            choices=self.categories
        )
        self.categoryCombo.SetSizerProps(expand=True)
        wx.StaticText(parent, -1, _("Tags"))
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
        wx.StaticText(parent, -1, _("Category"))
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
