# coding: utf-8

import wx
from pathlib import Path
from slugify import slugify
from bookworm.resources import sounds
from bookworm.logger import logger
from bookworm.gui.components import Dialog, SimpleDialog, DialogListCtrl
from .annotator import Bookmarker, NoteTaker, Book, Note, Bookmark
from .exporters import Exporter, export_completed


log = logger.getChild(__name__)


class BookmarksViewer(Dialog):
    """A ddialog to view the bookmarks of the current book."""

    def __init__(self, reader, annotator, *args, **kwargs):
        self.view = reader.view
        self.reader = reader
        self.annotator = annotator(self.reader)
        # Translators: label for unnamed bookmarks
        self._unamed_bookmark_title = _("(Unnamed)")
        super().__init__(*args, **kwargs)

    def addControls(self, sizer, parent):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        lstSizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        # Translators: the title of a dialog showing a list of bookmarks
        label = wx.StaticText(parent, -1, _("Saved Bookmarks"))
        self.annotationsListCtrl = DialogListCtrl(parent, -1)
        lstSizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 10)
        lstSizer.Add(
            self.annotationsListCtrl, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 10
        )
        # Translators: the label of a button to remove the selected item
        btnSizer.Add(wx.Button(parent, wx.ID_DELETE, _("&Remove")))
        mainSizer.Add(lstSizer, 1, wx.EXPAND | wx.ALL, 10)
        mainSizer.Add(btnSizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        sizer.Add(mainSizer, 1, wx.EXPAND | wx.ALL)
        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self.onItemClick, self.annotationsListCtrl
        )
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.onKeyDown, self.annotationsListCtrl)
        self.Bind(
            wx.EVT_LIST_END_LABEL_EDIT, self.onEndLabelEdit, self.annotationsListCtrl
        )
        self.Bind(wx.EVT_BUTTON, self.onDelete, id=wx.ID_DELETE)
        wx.FindWindowById(wx.ID_DELETE).Enable(False)
        self._populate_list()

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button to close the dialog
        btnsizer.AddButton(wx.Button(parent, wx.ID_CANCEL, _("&Close")))
        btnsizer.Realize()
        return btnsizer

    def _populate_list(self, focus_target=0):
        self.annotationsListCtrl.ClearAll()
        self.annotationsListCtrl.AppendColumn(
            # Translators: the title of a column in the bookmarks list
            _("Name"),
            format=wx.LIST_FORMAT_CENTER,
            width=20,
        )
        self.annotationsListCtrl.AppendColumn(
            # Translators: the title of a column in the bookmarks list
            _("Page"),
            format=wx.LIST_FORMAT_LEFT,
            width=50,
        )
        self.annotationsListCtrl.AppendColumn(
            # Translators: the title of a column in the bookmarks list
            _("Section"),
            format=wx.LIST_FORMAT_LEFT,
            width=30,
        )
        for i in range(3):
            self.annotationsListCtrl.SetColumnWidth(i, 100)
        annotations = self.annotator.get_list().all()
        for item in annotations:
            name = item.title or self._unamed_bookmark_title
            index = self.annotationsListCtrl.InsertItem(0, name)
            self.annotationsListCtrl.SetItem(index, 1, str(item.page_number + 1))
            self.annotationsListCtrl.SetItem(index, 2, item.section_title)
            self.annotationsListCtrl.SetItemData(index, item.id)
        page_annotations = self.annotator.get_for_page().all()
        section_annotations = self.annotator.get_for_section().all()
        if page_annotations:
            item_idx = self.annotationsListCtrl.FindItem(
                -1, data=page_annotations[0].id
            )
        elif section_annotations:
            item_idx = self.annotationsListCtrl.FindItem(
                -1, data=section_annotations[0].id
            )
        else:
            item_idx = focus_target
        self.setFocusToListItem(item_idx)
        self.FindWindowById(wx.ID_DELETE).Enable(len(annotations))

    @property
    def selectedItem(self):
        idx = self.annotationsListCtrl.GetFocusedItem()
        if idx != wx.NOT_FOUND:
            db_id = self.annotationsListCtrl.GetItemData(idx)
            return idx, db_id

    def setFocusToListItem(self, idx):
        self.annotationsListCtrl.SetFocus()
        self.annotationsListCtrl.EnsureVisible(idx)
        self.annotationsListCtrl.Select(idx)
        self.annotationsListCtrl.SetItemState(
            idx, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED
        )

    def onItemClick(self, event):
        if self.selectedItem is None:
            return
        item = self.annotator.get(self.selectedItem[1])
        self.reader.go_to_page(item.page_number)
        self.Close()
        wx.CallAfter(self.parent.contentTextCtrl.SetFocusFromKbd)
        wx.CallAfter(self.parent.contentTextCtrl.SetInsertionPoint, item.position)

    def onKeyDown(self, event):
        if self.selectedItem is None:
            return
        kcode = event.GetKeyCode()
        if kcode == wx.WXK_F2:
            selected = self.selectedItem
            if not selected:
                return
            item = selected[0]
            editCtrl = self.annotationsListCtrl.EditLabel(item)
            if (
                self.annotationsListCtrl.GetItemText(item)
                == self._unamed_bookmark_title
            ):
                editCtrl.SetValue("")
        elif kcode == wx.WXK_DELETE:
            self.onDelete(event)
        event.Skip()

    def onEndLabelEdit(self, event):
        newTitle = event.GetLabel()
        if newTitle != self._unamed_bookmark_title:
            self.annotator.update(item_id=self.selectedItem[1], title=newTitle)

    def onDelete(self, event):
        from . import AnnotationService

        if self.selectedItem is None:
            return
        if (
            wx.MessageBox(
                # Translators: the content of a message asking the user to delete a bookmark
                _(
                    "This action can not be reverted.\r\nAre you sure you want to remove this bookmark?"
                ),
                # Translators: the title of a message asking the user to delete a bookmark
                _("Remove Bookmark?"),
                parent=self,
                style=wx.YES_NO | wx.ICON_WARNING,
            )
            == wx.YES
        ):
            item = self.annotator.get(self.selectedItem[1])
            page_number, pos = item.page_number, item.position
            self.annotator.delete(self.selectedItem[1])
            self._populate_list()
            if page_number == self.reader.current_page:
                AnnotationService.style_bookmark(self.Parent, pos, enable=False)


class AnnotationFilterDialog(SimpleDialog):
    pass


class ExportNotesDialog(Dialog):
    """Customization for note exporting."""

    def __init__(self, reader, *args, **kwargs):
        self.reader = reader
        self.annotator = NoteTaker(reader)
        super().__init__(*args, **kwargs)

    def addControls(self, sizer, parent):
        # Translators: the label of a radio button
        self.output_ranges = [_("Whole Book"), _("Current Section")]
        formats = [_(rend.display_name) for rend in NotesExporter.renderers]
        self.outputRangeRb = wx.RadioBox(
            parent,
            -1,
            # Translators: the title of a group of radio buttons in the Export Notes dialog
            _("Export Range"),
            choices=self.output_ranges,
            majorDimension=2,
            style=wx.RA_SPECIFY_COLS,
        )
        # Translators: the label of a combobox of available export formats
        formatChoiceLabel = wx.StaticText(parent, -1, _("Output format:"))
        self.formatChoice = wx.Choice(parent, -1, choices=formats)
        self.openAfterExportCheckBox = wx.CheckBox(
            parent,
            -1,
            # Translators: the label of a checkbox
            _("Open file after exporting"),
        )
        sizer.Add(self.outputRangeRb, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(formatChoiceLabel, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(self.formatChoice, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.openAfterExportCheckBox, 0, wx.EXPAND | wx.ALL, 10)
        self.formatChoice.SetSelection(0)
        self.openAfterExportCheckBox.SetValue(True)
        self.Bind(wx.EVT_BUTTON, self.onSubmit, id=wx.ID_SAVE)

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button in the Export Notes dialog
        export_btn = wx.Button(parent, wx.ID_SAVE, _("&Export"))
        export_btn.SetDefault()
        btnsizer.AddButton(export_btn)
        # Translators: the label of a button to cancel the current action
        btnsizer.AddButton(wx.Button(parent, wx.ID_CANCEL, _("&Cancel")))
        btnsizer.Realize()
        return btnsizer

    def onSubmit(self, event):
        suffix = self.reader.current_book.title
        renderer = NotesExporter.renderers[self.formatChoice.GetSelection()]
        if self.outputRangeRb.GetSelection() == 0:
            notes = self.annotator.get_list(asc=True)
        else:
            notes = self.annotator.get_for_section(
                self.reader.active_section.unique_identifier, asc=True
            )
            pager = self.reader.active_section.pager
            suffix += f" {pager.first + 1}-{pager.last + 1}"
        if not notes.count():
            wx.MessageBox(
                # Translators: the content of a message dialog
                _(
                    "There are no notes for this book or the selected section.\n"
                    "Please make sure you have added some notes before using the export functionality."
                ),
                # Translators: the title of a message dialog
                _("No Notes"),
                style=wx.ICON_WARNING,
            )
            return self.Close()
        filename = slugify(suffix) + renderer.output_ext
        saveExportedFD = wx.FileDialog(
            self,
            # Translators: the title of a save file dialog asking the user for a filename to export notes to
            _("Export To"),
            defaultDir=wx.GetUserHome(),
            defaultFile=filename,
            wildcard=f"{_(renderer.display_name)} (*{renderer.output_ext})|{renderer.output_ext}",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        if saveExportedFD.ShowModal() != wx.ID_OK:
            return
        file_path = saveExportedFD.GetPath().strip()
        saveExportedFD.Destroy()
        try:
            file_path = file_path.encode("mbcs")
        except UnicodeEncodeError:
            wx.MessageBox(
                # Translators: the content of a message telling the user that the file name is invalid
                _(
                    "The provided file name is not valid. Please try again with a different name."
                ),
                # Translators: the title of a message telling the user that the provided file name is invalid
                _("Invalid File Name"),
                style=wx.ICON_ERROR,
            )
            self.fileCtrl.SetValue("")
            self.fileCtrl.SetFocus()
            return
        exporter = NotesExporter(
            renderer_name=renderer.name,
            notes=notes,
            doc_title=self.reader.current_book.title,
            filename=file_path,
        )
        self.shouldOpenAfterExport = self.openAfterExportCheckBox.GetValue()
        export_completed.connect(self.onExportCompleted, sender=exporter)
        exporter.render_to_file()
        self.Close()

    def onExportCompleted(self, sender, filename):
        if self.shouldOpenAfterExport:
            wx.LaunchDefaultApplication(document=filename)
