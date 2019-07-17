# coding: utf-8

import wx
from pathlib import Path
from slugify import slugify
from bookworm import sounds
from bookworm.annotator import Bookmarker, NoteTaker, Book, Note, Bookmark
from bookworm.notes_exporter import NotesExporter
from bookworm.signals import notes_export_completed
from bookworm.logger import logger
from ..components import Dialog, DialogListCtrl


log = logger.getChild(__name__)


def _annotations_page_handler(reader):
    q_count = (
        Note.query.filter(Book.identifier == reader.document.identifier)
        .filter_by(page_number=reader.current_page)
        .count()
    )
    if q_count:
        sounds.has_note.play()


def play_sound_if_note(sender, current, prev):
    """Play a sound if the current page has a note."""
    wx.CallLater(150, _annotations_page_handler, sender)


def highlight_bookmarked_positions(sender, current, prev):
    bookmarks = (
        Bookmark.query.filter(Book.identifier == sender.document.identifier)
        .filter(Bookmark.page_number == sender.current_page)
        .all()
    )
    if not bookmarks:
        return
    for bookmark in bookmarks:
        highlight_containing_line(bookmark.position, sender.view)


def highlight_containing_line(pos, view):
    lft, rgt = view.get_containing_line(pos)
    wx.CallAfter(
        view.contentTextCtrl.SetStyle, lft, rgt, wx.TextAttr(wx.WHITE, wx.BLACK)
    )


class ViewAnnotationsDialog(Dialog):
    """Annotations viewer."""

    def __init__(self, parent, type_, *args, **kwargs):
        self.type = type_
        self.reader = parent.reader
        annotatorFactory = Bookmarker if type_ == "bookmark" else NoteTaker
        self.annotator = annotatorFactory(self.reader)
        super().__init__(parent, *args, **kwargs)

    def addControls(self, sizer, parent):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        lstSizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(
            parent, -1, "Bookmarks" if self.type == "bookmark" else "Notes"
        )
        self.annotationsListCtrl = DialogListCtrl(parent, -1)
        lstSizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 10)
        lstSizer.Add(
            self.annotationsListCtrl, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 10
        )
        if self.type == "note":
            btnSizer.Add(wx.Button(parent, wx.ID_PREVIEW, "&View"))
            btnSizer.Add(wx.Button(parent, wx.ID_EDIT, "&Edit..."))
        btnSizer.Add(wx.Button(parent, wx.ID_DELETE, "&Remove"))
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
        if self.type == "note":
            self.Bind(wx.EVT_BUTTON, self.onView, id=wx.ID_PREVIEW)
            self.Bind(wx.EVT_BUTTON, self.onEdit, id=wx.ID_EDIT)
        self.btns = [
            wx.FindWindowById(i) for i in (wx.ID_DELETE, wx.ID_PREVIEW, wx.ID_EDIT)
        ]
        self.btns = [b for b in self.btns if (b is not None) and b.Parent == parent]
        [b.Enable(False) for b in self.btns]
        self._populate_list()

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(wx.Button(parent, wx.ID_CANCEL, "&Close"))
        btnsizer.Realize()
        return btnsizer

    def _populate_list(self, focus_target=0):
        self.annotationsListCtrl.ClearAll()
        self.annotationsListCtrl.AppendColumn(
            "Title", format=wx.LIST_FORMAT_LEFT, width=50
        )
        self.annotationsListCtrl.AppendColumn(
            "Page", format=wx.LIST_FORMAT_CENTER, width=20
        )
        self.annotationsListCtrl.AppendColumn(
            "Section", format=wx.LIST_FORMAT_LEFT, width=30
        )
        self.annotationsListCtrl.SetColumnWidth(0, 100)
        self.annotationsListCtrl.SetColumnWidth(1, 100)
        self.annotationsListCtrl.SetColumnWidth(2, 100)
        annotations = self.annotator.get_list().all()
        for anotation in annotations:
            index = self.annotationsListCtrl.InsertItem(0, anotation.title)
            self.annotationsListCtrl.SetItem(index, 1, str(anotation.page_number + 1))
            self.annotationsListCtrl.SetItem(index, 2, anotation.section_title)
            self.annotationsListCtrl.SetItemData(index, anotation.id)
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
        should_enable = len(annotations)
        [btn.Enable(should_enable) for btn in self.btns]

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
        wx.CallAfter(self.parent.contentTextCtrl.SetInsertionPoint, item.position)

    def onKeyDown(self, event):
        if self.selectedItem is None:
            return
        kcode = event.GetKeyCode()
        if kcode == wx.WXK_F2:
            self.annotationsListCtrl.EditLabel(self.selectedItem[0])
        elif kcode == wx.WXK_DELETE:
            self.onDelete(event)
        event.Skip()

    def onEndLabelEdit(self, event):
        newTitle = event.GetLabel()
        self.annotator.update(item_id=self.selectedItem[1], title=newTitle)

    def onDelete(self, event):
        if self.selectedItem is None:
            return
        if (
            wx.MessageBox(
                "This action can not be reverted.\r\nAre you sure you want to continue?",
                "Remove Entry?",
                parent=self,
                style=wx.YES_NO | wx.ICON_WARNING,
            )
            == wx.YES
        ):
            item = self.annotator.get(self.selectedItem[1])
            page_number, pos = item.page_number, item.position
            self.annotator.delete(self.selectedItem[1])
            self._populate_list()
            if self.type == "bookmark":
                if page_number == self.reader.current_page:
                    lft, rgt = self.reader.view.get_containing_line(pos)
                    self.Parent.clear_highlight(lft, rgt)

    def onView(self, event):
        assert self.type == "note", "Viewing is only allowed for notes."
        if self.selectedItem is None:
            return
        note = self.annotator.get(self.selectedItem[1])
        dlg = NoteEditorDialog(self, self.reader, note=note, view_only=True)
        dlg.ShowModal()

    def onEdit(self, event):
        assert self.type == "note", "Editing is only allowed for notes."
        if self.selectedItem is None:
            return
        note = self.annotator.get(self.selectedItem[1])
        dlg = NoteEditorDialog(self, self.reader, note=note)
        dlg.ShowModal()
        self._populate_list()


class NoteEditorDialog(Dialog):
    """Create and edit notes."""

    def __init__(self, parent, reader, note=None, pos=0, view_only=False, **kwargs):
        self.annotator = NoteTaker(reader)
        self.reader = reader
        self.note = note
        self.cursorPos = pos
        self.view_only = view_only
        if self.view_only:
            prefix = "View"
        elif self.note is None:
            prefix = "Take"
        else:
            prefix = "Edit"
        super().__init__(parent, title=f"{prefix} Note", **kwargs)

    def addControls(self, sizer, parent):
        vsizer = wx.BoxSizer(wx.VERTICAL)
        titleLabel = wx.StaticText(parent, -1, "Note Title:")
        self.titleTextCtrl = wx.TextCtrl(parent, -1)
        contentLabel = wx.StaticText(parent, -1, "Note Content:")
        self.noteContentTextCtrl = wx.TextCtrl(
            parent, -1, style=wx.TE_MULTILINE | wx.TE_RICH2
        )
        vsizer.Add(titleLabel, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        vsizer.Add(self.titleTextCtrl, 0, wx.ALL | wx.EXPAND, 10)
        vsizer.Add(contentLabel, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        vsizer.Add(self.noteContentTextCtrl, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(vsizer, 1, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.onSaveNote, id=wx.ID_OK)
        if self.note is not None:
            self.titleTextCtrl.SetValue(self.note.title)
            self.noteContentTextCtrl.SetValue(self.note.content)
        if self.view_only:
            for te in (self.titleTextCtrl, self.noteContentTextCtrl):
                te.SetEditable(False)
            self.titleTextCtrl.SetFocus()

    def getButtons(self, parent):
        if self.view_only:
            btnsizer = wx.StdDialogButtonSizer()
            btnsizer.AddButton(wx.Button(parent, wx.ID_CANCEL, "&Close"))
            btnsizer.Realize()
            return btnsizer
        return super().getButtons(parent)

    def onSaveNote(self, event):
        title = self.titleTextCtrl.GetValue().strip()
        content = self.noteContentTextCtrl.GetValue().strip()
        if not all((title, content)):
            wx.MessageBox(
                "Could not save note. Empty fields are present",
                "Warning",
                parent=self,
                style=wx.ICON_WARNING,
            )
            return
        kwargs = dict(title=title, content=content)
        if self.note is not None:
            self.annotator.update(item_id=self.note.id, **kwargs)
        else:
            kwargs.update(
                dict(
                    position=self.cursorPos,
                    section_title=self.reader.active_section.title,
                    page_number=self.reader.current_page,
                )
            )
            self.annotator.create(**kwargs)
        self.Close()


class ExportNotesDialog(Dialog):
    """Customization for note exporting."""

    def __init__(self, reader, *args, **kwargs):
        self.reader = reader
        self.annotator = NoteTaker(reader)
        super().__init__(*args, **kwargs)

    def addControls(self, sizer, parent):
        self.output_ranges = ["Whole Book", "Current Section"]
        formats = [rend.display_name for rend in NotesExporter.renderers]
        self.outputRangeRb = wx.RadioBox(
            parent,
            -1,
            "Export Range",
            choices=self.output_ranges,
            majorDimension=2,
            style=wx.RA_SPECIFY_COLS,
        )
        formatChoiceLabel = wx.StaticText(parent, -1, "Output Format:")
        self.formatChoice = wx.Choice(parent, -1, choices=formats)
        self.openAfterExportCheckBox = wx.CheckBox(
            parent, -1, "Open file after exporting"
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
        export_btn = wx.Button(parent, wx.ID_SAVE, "&Export")
        export_btn.SetDefault()
        btnsizer.AddButton(export_btn)
        btnsizer.AddButton(wx.Button(parent, wx.ID_CANCEL, "&Cancel"))
        btnsizer.Realize()
        return btnsizer

    def onSubmit(self, event):
        suffix = self.reader.get_view_title()
        renderer = NotesExporter.renderers[self.formatChoice.GetSelection()]
        if self.outputRangeRb.GetSelection() == 0:
            notes = self.annotator.get_list(asc=True)
        else:
            notes = self.annotator.get_for_section(
                self.reader.active_section.unique_identifier, asc=True
            )
            pager = self.reader.active_section.pager
            suffix += f" {pager.first + 1}-{pager.last + 1}"
        filename = slugify(suffix) + renderer.output_ext
        saveExportedFD = wx.FileDialog(
            self,
            "Export To",
            defaultDir=wx.GetUserHome(),
            defaultFile=filename,
            wildcard=f"{renderer.display_name} (*{renderer.output_ext})|{renderer.output_ext}",
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
                "Invalid file name. Please try again.", "Error", style=wx.ICON_ERROR
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
        notes_export_completed.connect(self.onExportCompleted, sender=exporter)
        exporter.render_to_file()
        self.Close()

    def onExportCompleted(self, sender, filename):
        if self.shouldOpenAfterExport:
            wx.LaunchDefaultApplication(document=filename)
