# coding: utf-8

import wx
import wx.lib.sized_controls as sc
from pathlib import Path
from slugify import slugify
from bookworm.utils import format_datetime
from bookworm.resources import sounds
from bookworm.logger import logger
from bookworm.gui.components import (
    Dialog,
    SimpleDialog,
    ImmutableObjectListView,
    ColumnDefn,
    make_sized_static_box,
)
from .annotator import Bookmarker, NoteTaker, Quoter, Book, Note, Bookmark
from .exporters import Exporter, export_completed


log = logger.getChild(__name__)


class ViewAndEditAnnotationDialog(SimpleDialog):

    def __init__(self, *args, annotation, editable=False, **kwargs):
        self.annotation = annotation
        self.editable = editable
        self.__saving = False
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        parent.SetMinSize((500, -1))
        parent.Layout()
        parent.Fit()
        CAN_EDIT = 0 if self.editable else wx.TE_READONLY
        wx.StaticText(parent, -1, _("Content"))
        self.contentText = wx.TextCtrl(parent, -1, style=CAN_EDIT|wx.TE_MULTILINE)
        self.contentText.SetSizerProps(expand=True)
        metadataBox = make_sized_static_box(parent, _("Metadata"))
        metadataBox.SetSizerProps(expand=True)
        wx.StaticText(metadataBox, -1, _("Tags"))
        self.tagsText = wx.TextCtrl(metadataBox, -1, style=CAN_EDIT|wx.TE_MULTILINE)
        self.tagsText.SetSizerProps(expand=True)
        if not self.editable:
            wx.StaticText(metadataBox, -1, _("Date Created"))
            self.createdText = wx.TextCtrl(metadataBox, -1, style=wx.TE_READONLY|wx.TE_MULTILINE)
            self.createdText.SetSizerProps(expand=True)
            wx.StaticText(metadataBox, -1, _("Last updated"))
            self.updatedText = wx.TextCtrl(metadataBox, -1, style=wx.TE_READONLY|wx.TE_MULTILINE)
            self.updatedText.SetSizerProps(expand=True)
        if self.editable:
            self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)
        self.set_values()
    
    def getButtons(self, parent):
        if self.editable:
            return super().getButtons(parent)
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button to close the dialog
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        btnsizer.Realize()
        return btnsizer

    def set_values(self):
        self.contentText.Value = self.annotation.content
        self.tagsText.Value = " ".join(self.annotation.tags)
        if not self.editable:
            self.createdText.Value = format_datetime(self.annotation.date_created)
            self.updatedText.Value = format_datetime(self.annotation.date_updated)

    def get_values(self):
        assert self.editable, "Read only mode."
        tags = [t.strip() for t in self.tagsText.GetValue().split()]
        return dict(
            content=self.contentText.GetValue().strip(),
            tags=tags
        )

    def onOk(self, event):
        self.__saving = True
        self.Close()

    def ShowModal(self):
        super().ShowModal()
        if self.editable and self.__saving:
            return self.get_values()



class BookmarksViewer(SimpleDialog):
    """A ddialog to view the bookmarks of the current book."""

    def __init__(self, reader, annotator, *args, **kwargs):
        self.view = reader.view
        self.reader = reader
        self.annotator = annotator(self.reader)
        # Translators: label for unnamed bookmarks
        self._unamed_bookmark_title = _("(Unnamed)")
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        wx.StaticText(parent, -1, _("Saved Bookmarks"))
        self.annotationsListCtrl = ImmutableObjectListView(parent, wx.ID_ANY)
        wx.Button(parent, wx.ID_DELETE, _("&Remove"))
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
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        btnsizer.Realize()
        return btnsizer

    def _populate_list(self, focus_target=0):
        annotations = self.annotator.get_list().all()
        self.annotationsListCtrl.set_columns(
            [
                # Translators: the title of a column in the bookmarks list
                ColumnDefn(_("Name"), "left", 250, "title"),
                # Translators: the title of a column in the bookmarks list
                ColumnDefn(_("Page"), "center", 150, "page_number"),
                # Translators: the title of a column in the bookmarks list
                ColumnDefn(_("Section"), "left", 250, "section_title"),
            ]
        )
        self.annotationsListCtrl.set_objects(annotations)
        self.FindWindowById(wx.ID_DELETE).Enable(len(annotations))

    def onItemClick(self, event):
        item = self.annotationsListCtrl.get_selected()
        if item is None:
            return
        self.reader.go_to_page(item.page_number)
        self.Close()
        wx.CallAfter(self.parent.contentTextCtrl.SetFocusFromKbd)
        wx.CallAfter(self.parent.contentTextCtrl.SetInsertionPoint, item.position)

    def onKeyDown(self, event):
        item = self.annotationsListCtrl.get_selected()
        if item is None:
            return
        selected_idx = self.annotationsListCtrl.GetFocusedItem()
        kcode = event.GetKeyCode()
        if kcode == wx.WXK_F2:
            editCtrl = self.annotationsListCtrl.EditLabel(selected_idx)
            if (
                self.annotationsListCtrl.GetItemText(selected_idx)
                == self._unamed_bookmark_title
            ):
                editCtrl.SetValue("")
        elif kcode == wx.WXK_DELETE:
            self.onDelete(event)
        event.Skip()

    def onEndLabelEdit(self, event):
        newTitle = event.GetLabel()
        if newTitle != self._unamed_bookmark_title:
            self.annotator.update(
                item_id=self.annotationsListCtrl.get_selected().id, title=newTitle
            )

    def onDelete(self, event):
        from . import AnnotationService

        item = self.annotationsListCtrl.get_selected()
        if item is None:
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
            page_number, pos = item.page_number, item.position
            self.annotator.delete(item.id)
            self._populate_list()
            if page_number == self.reader.current_page:
                AnnotationService.style_bookmark(self.Parent, pos, enable=False)


class AnnotationFilterPanel(sc.SizedPanel):
    """Filter by several criteria."""

    def __init__(self, *args, annotator, filter_callback, **kwargs):
        super().__init__(*args, **kwargs)
        self.SetSizerProps(expand=True)
        self.SetSizerType("horizontal")
        self.annotator = annotator
        self.filter_callback = filter_callback
        # Translators: the header of the filtering controls in the annotations viewer
        wx.StaticText(self, -1, _("Tag"))
        self.GetSizer().AddSpacer(10)
        self.tagsCombo = wx.ComboBox(self, -1)
        self.GetSizer().AddSpacer(20)
        wx.StaticText(self, -1, _("Section"))
        self.GetSizer().AddSpacer(10)
        self.sectionChoice = wx.ComboBox(self, -1)
        self.GetSizer().AddSpacer(20)
        wx.StaticText(self, -1, _("Content"))
        self.GetSizer().AddSpacer(10)
        self.contentFilterText = wx.TextCtrl(self, -1)
        self.GetSizer().AddSpacer(20)
        applyFilterButton = wx.Button(self, -1, _("Apply &Filter"))
        self.Bind(wx.EVT_BUTTON, self.onApplyFilter, applyFilterButton)
        self.update_choices()

    def update_choices(self):
        self.tagsCombo.Clear()
        self.sectionChoice.Clear()
        self.tagsCombo.AppendItems(self.annotator.get_tags())
        self.sectionChoice.AppendItems([s[0] for s in self.annotator.get_sections()])

    def SetFocus(self):
        self.tagsCombo.SetFocus()

    def onApplyFilter(self, event):
        self.filter_callback(
            tag=self.tagsCombo.GetValue().strip(),
            section_title=self.sectionChoice.GetValue().strip(),
            content=self.contentFilterText.GetValue().strip(),
        )


class AnnotationWithContentDialog(SimpleDialog):
    """View, edit, and manage notes and quotes."""

    annotator_cls = None
    can_edit = False
    column_defns = [
        ColumnDefn("Excerpt", "left", 250, "content"),
        ColumnDefn("Section", "left", 200, "section_title"),
        ColumnDefn("Page", "center", 150, "page_number"),
        ColumnDefn("Added", "right", 180, lambda a: format_datetime(a.date_created)),
    ]

    def __init__(self, reader, *args, **kwargs):
        self.reader = reader
        self.annotator = self.annotator_cls(reader)
        self.service = wx.GetApp().service_handler.get_service("annotation")
        self.__last_filter = ("", "", "")
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        filterBox = make_sized_static_box(parent, _("Filter"))
        self.filterPanel = AnnotationFilterPanel(
            filterBox, -1, annotator=self.annotator, filter_callback=self.onFilter
        )
        wx.StaticText(parent, -1, self.Title)
        self.itemsView = ImmutableObjectListView(
            parent, id=wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER
        )
        self.buttonPanel = sc.SizedPanel(parent, -1)
        self.buttonPanel.SetSizerType("horizontal")
        wx.Button(self.buttonPanel, wx.ID_PREVIEW, _("&View..."))
        if self.can_edit:
            wx.Button(self.buttonPanel, wx.ID_EDIT, _("&Edit..."))
            self.Bind(wx.EVT_BUTTON, self.onEdit, id=wx.ID_EDIT)
        wx.Button(self.buttonPanel, wx.ID_DELETE, _("&Delete..."))
        exportButton = wx.Button(self.buttonPanel, -1, _("E&xport Annotations..."))
        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self.onItemClick, self.itemsView
        )
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.onKeyDown, self.itemsView)
        self.Bind(
            wx.EVT_BUTTON, self.onView, id=wx.ID_PREVIEW
        )
        self.Bind(wx.EVT_BUTTON, self.onDelete, id=wx.ID_DELETE)
        self.Bind(wx.EVT_BUTTON, self.onExport, exportButton)
        self.set_items()

    def set_items(self, items=None):
        items = items or self.get_items()
        self.itemsView.set_columns(self.column_defns)
        self.itemsView.set_objects(items)
        self.itemsView.SetFocusFromKbd()
        if not self.itemsView.ItemCount:
            self.buttonPanel.Disable()

    def onFilter(self, tag, section_title, content):
        self.__last_filter = (tag, section_title, content)
        self.set_items(self.get_items())

    def get_items(self):
        if any(self.__last_filter):
            return self.annotator.get_filtered_for_book(*self.__last_filter)
        return self.annotator.get_list().all()

    def go_to_item(self, item):
        self.reader.go_to_page(item.page_number)

    def onItemClick(self, event):
        item = self.itemsView.get_selected()
        if item is not None:
            self.Close()
            self.go_to_item(item)

    def view_or_edit(self, is_viewing=True):
        item = self.itemsView.get_selected()
        if item is None:
            return wx.Bell()
        editable = self.can_edit and not is_viewing
        dlg = ViewAndEditAnnotationDialog(
            self, title=_("Annotation"), annotation=item, editable=editable
        )
        with dlg:
            return dlg.ShowModal()

    def onView(self, event):
        self.view_or_edit(is_viewing=True)

    def onDelete(self, event):
        item = self.itemsView.get_selected()
        if item is None:
            return
        if wx.MessageBox(
            _("This action can not be reverted.\r\nAre you sure you want to remove this item?"),
            _("Delete Annotation?"),
            parent=self,
            style=wx.YES_NO | wx.ICON_WARNING,
        ) == wx.YES:
            self.annotator.delete(item.id)
            self.filterPanel.update_choices()
            self.set_items(self.get_items())

    def onEdit(self, event):
        if not self.can_edit:
            return
        updates = self.view_or_edit(is_viewing=False)
        if updates:
            item = self.itemsView.get_selected()
            self.annotator.update(item.id, **updates)
            self.filterPanel.update_choices()
            self.set_items()

    def onKeyDown(self, event):
        item = self.itemsView.get_selected()
        if item is None:
            return
        kcode = event.GetKeyCode()
        if kcode == wx.WXK_DELETE:
            self.onDelete(event)
        elif kcode == wx.WXK_F6:
            self.filterPanel.SetFocus()
        event.Skip()

    def onExport(self, event):
        items = tuple(self.get_items())
        if not items:
            return


class CommentsDialog(AnnotationWithContentDialog):
    annotator_cls = NoteTaker
    can_edit = True

    def go_to_item(self, item):
        super().go_to_item(item)
        self.service.view.set_insertion_point(item.position)

class QuotesDialog(AnnotationWithContentDialog):
    annotator_cls = Quoter
    can_edit = False

    def go_to_item(self, item):
        super().go_to_item(item)
        self.service.view.select_text(item.start_pos, item.end_pos)


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
