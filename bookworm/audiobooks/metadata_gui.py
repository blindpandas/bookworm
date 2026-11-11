"""Native tag tree: each scalar value is edited in a labeled native control."""

import copy
import math
import tempfile
from pathlib import Path

import wx
from mutagen.id3 import Frames
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4Cover

from .metadata import TagNode, decode_v1, encode_v1, field_name, make_node, node_value


def atomic_write(path, data):
    path = Path(path)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=".bookworm-data-", delete=False
    ) as output:
        temporary = Path(output.name)
        output.write(data)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def save_report(parent, text):
    with wx.FileDialog(
        parent,
        _("Save file information as text"),
        defaultFile="audio-information.txt",
        wildcard=_("Text files") + "|*.txt",
        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
    ) as dialog:
        if dialog.ShowModal() != wx.ID_OK:
            return
        path = Path(dialog.Path)
    if path.suffix.casefold() != ".txt":
        raise ValueError(_("Use the .txt extension for the information report."))
    atomic_write(path, text.encode("utf-8-sig"))


class FileInformationDialog(wx.Dialog):
    def __init__(self, parent, document):
        super().__init__(
            parent,
            title=_("Audio file information"),
            size=(750, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        box = wx.BoxSizer(wx.VERTICAL)
        text = document.report()
        self.report = wx.TextCtrl(
            self,
            value=text,
            style=wx.TE_READONLY | wx.TE_MULTILINE,
            name=_("Audio file information"),
        )
        self.report.SetName(_("Audio file information"))
        box.Add(self.report, 1, wx.EXPAND | wx.ALL, 12)
        button = wx.Button(self, label=_("Save as &text…"))
        button.Bind(wx.EVT_BUTTON, lambda _event: parent.guarded(lambda: save_report(self, text)))
        box.Add(button, 0, wx.ALL, 6)
        box.Add(self.CreateButtonSizer(wx.OK), 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(box)
        self.report.SetInsertionPoint(0)
        self.report.SetFocus()


class V1Dialog(wx.Dialog):
    def __init__(self, parent, raw):
        super().__init__(parent, title=_("ID3v1 fields"))
        self.raw = raw
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(wx.StaticText(self, label=_("ID3v1 character encoding")), 0, wx.TOP, 6)
        self.encoding = wx.Choice(
            self,
            choices=[_("ISO-8859-1 (legacy standard)"), _("Windows-1250 (Hungarian legacy tags)")],
            name=_("ID3v1 character encoding"),
        )
        self.encoding.SetSelection(0)
        box.Add(self.encoding, 0, wx.EXPAND)
        self.controls = {}
        for key, value in decode_v1(raw).items():
            label = field_name(key)
            box.Add(wx.StaticText(self, label=label), 0, wx.TOP, 6)
            control = wx.TextCtrl(self, value=str(value), name=label)
            control.SetName(label)
            self.controls[key] = control
            box.Add(control, 0, wx.EXPAND)
        box.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL, 12)
        self.SetSizerAndFit(box)
        self.encoding.Bind(wx.EVT_CHOICE, self.change_encoding)
        self.Bind(wx.EVT_BUTTON, self.accept, id=wx.ID_OK)

    def change_encoding(self, _event):
        # Reinterpret original bytes only; require acknowledgement before
        # replacing any text the user may already have entered.
        if (
            wx.MessageBox(
                _(
                    "Reload the original ID3v1 bytes using this character encoding? Unsaved edits in this window will be replaced."
                ),
                _("ID3v1 fields"),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            == wx.YES
        ):
            values = decode_v1(self.raw, "cp1250" if self.encoding.Selection else "latin-1")
            for key, value in values.items():
                self.controls[key].ChangeValue(str(value))

    def accept(self, _event):
        try:
            self.raw = encode_v1(
                {k: c.Value for k, c in self.controls.items()},
                "cp1250" if self.encoding.Selection else "latin-1",
            )
        except (ValueError, UnicodeError) as exc:
            wx.MessageBox(str(exc), _("ID3v1 fields"), wx.OK | wx.ICON_ERROR, self)
            return
        self.EndModal(wx.ID_OK)


class TagEditorDialog(wx.Dialog):
    def __init__(self, parent, document):
        super().__init__(
            parent,
            title=_("Edit audio tags"),
            size=(800, 700),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.document = document
        self.v1 = None  # Preserve original bytes unless explicitly changed.
        self.roots = [document.tags]
        if hasattr(document.audio, "pictures"):
            self.roots.append(TagNode(_("Cover art"), "list", children=document.pictures))
        box = wx.BoxSizer(wx.VERTICAL)
        self.tree = wx.TreeCtrl(
            self,
            style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_HIDE_ROOT,
            name=_("Audio tag fields"),
        )
        self.tree.SetName(_("Audio tag fields"))
        box.Add(self.tree, 1, wx.EXPAND | wx.ALL, 10)
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, lambda _event: parent.guarded(self.edit))
        self.details = wx.TextCtrl(
            self, style=wx.TE_MULTILINE | wx.TE_READONLY, name=_("Selected tag value")
        )
        self.details.SetName(_("Selected tag value"))
        box.Add(self.details, 0, wx.EXPAND | wx.ALL, 8)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.select)
        row = wx.WrapSizer(wx.HORIZONTAL)
        for label, action in (
            (_("&Edit value…"), self.edit),
            (_("&Add field or value…"), self.add),
            (_("&Remove field or value"), self.remove),
            (_("Export &binary value…"), self.export_binary),
            (_("Save as &text…"), lambda: save_report(self, document.report())),
        ):
            button = wx.Button(self, label=label)
            button.Bind(wx.EVT_BUTTON, lambda _event, a=action: parent.guarded(a))
            row.Add(button, 0, wx.ALL, 4)
        box.Add(row, 0, wx.EXPAND)
        self.version = None
        if document.tags.kind == "id3":
            box.Add(wx.StaticText(self, label=_("ID3v2 save version")))
            self.version = wx.Choice(
                self, choices=["ID3v2.3", "ID3v2.4"], name=_("ID3v2 save version")
            )
            self.version.SetSelection(0 if document.version == 3 else 1)
            box.Add(self.version)
        if isinstance(document.audio, MP3):
            row = wx.WrapSizer(wx.HORIZONTAL)
            for label, action in (
                (_("Edit ID3&v1…"), self.edit_v1),
                (_("Remove ID3v1"), self.remove_v1),
            ):
                button = wx.Button(self, label=label)
                button.Bind(wx.EVT_BUTTON, lambda _event, a=action: parent.guarded(a))
                row.Add(button, 0, wx.ALL, 4)
            box.Add(row)
        warning = wx.StaticText(
            self,
            label=_(
                "Saving creates a verified backup and checks that the encoded audio is unchanged. Unknown ID3 frames are preserved. Cancel discards edits."
            ),
        )
        warning.Wrap(740)
        box.Add(warning, 0, wx.ALL, 8)
        box.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(box)
        self.Bind(wx.EVT_BUTTON, self.accept, id=wx.ID_OK)
        self.refresh()
        self.tree.SetFocus()

    def refresh(self, selected=None):
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot(_("Audio tag fields"))

        def append(parent, node, owner):
            title = field_name(node.name.split(":", 1)[0])
            if node.kind not in ("frame", "id3", "mapping", "list", "tuple", "binary"):
                title += ": " + str(node.value).replace("\n", " ")[:180]
            item = self.tree.AppendItem(parent, title, data=(node, owner))
            for child in node.children:
                append(item, child, node)
            if node.kind in ("id3", "mapping"):
                self.tree.Expand(item)
            if node is selected:
                self.tree.SelectItem(item)
                self.tree.EnsureVisible(item)

        for node in self.roots:
            append(root, node, None)
        if not self.tree.GetSelection().IsOk():
            first, _cookie = self.tree.GetFirstChild(root)
            self.tree.SelectItem(first)

    def selection(self):
        item = self.tree.GetSelection()
        return self.tree.GetItemData(item) if item.IsOk() else (None, None)

    def select(self, event):
        node, _owner = self.selection()
        if node:
            self.details.ChangeValue("\n".join(self.document._node_lines(node)))
        event.Skip()

    def edit(self):
        node, owner = self.selection()
        if node is None:
            return
        if node.kind in ("frame", "id3", "mapping", "list", "tuple"):
            self.tree.Expand(self.tree.GetSelection())
            return
        if node.kind == "binary":
            with wx.FileDialog(
                self,
                _("Import binary tag value"),
                wildcard=_("Tag data and pictures") + "|*.bin;*.jpg;*.jpeg;*.png",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                path = Path(dialog.Path)
            if path.stat().st_size > 32 * 1024 * 1024:
                raise ValueError(_("A binary tag value must not exceed 32 MiB."))
            node.value = path.read_bytes()
            if isinstance(node.template, MP4Cover) or (owner and owner.name == "covr"):
                if node.value.startswith(b"\x89PNG\r\n\x1a\n"):
                    node.template = MP4Cover(node.value, imageformat=MP4Cover.FORMAT_PNG)
                elif node.value.startswith(b"\xff\xd8\xff"):
                    node.template = MP4Cover(node.value, imageformat=MP4Cover.FORMAT_JPEG)
                else:
                    raise ValueError(_("An MP4 cover must be a JPEG or PNG image."))
        elif node.kind == "boolean":
            with wx.SingleChoiceDialog(
                self, field_name(node.name), _("Edit tag value"), [_("No"), _("Yes")]
            ) as dialog:
                dialog.SetSelection(int(node.value))
                if dialog.ShowModal() != wx.ID_OK:
                    return
                node.value = bool(dialog.Selection)
        else:
            with wx.TextEntryDialog(
                self,
                field_name(node.name),
                _("Edit tag value"),
                str(node.value),
                style=wx.OK | wx.CANCEL | wx.TE_MULTILINE,
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                value = dialog.Value
            if node.kind == "integer":
                try:
                    value = int(value)
                except ValueError as exc:
                    raise ValueError(_("Please enter an integer.")) from exc
            elif node.kind == "number":
                try:
                    value = float(value.replace(",", "."))
                except ValueError as exc:
                    raise ValueError(_("Please enter a finite number.")) from exc
                if not math.isfinite(value):
                    raise ValueError(_("Please enter a finite number."))
            node.value = value
        self.refresh(node)

    def add(self):
        node, _owner = self.selection()
        if node is None:
            return
        if node.kind == "id3":
            names = sorted(Frames)
            with wx.SingleChoiceDialog(
                self, _("ID3 field type"), _("Add tag field"), [field_name(n) for n in names]
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                code = names[dialog.Selection]
            added = make_node(code, Frames[code]())
        elif node.kind == "frame":
            existing = {c.name for c in node.children}
            specs = [
                s
                for s in node.value._framespec + node.value._optionalspec
                if s.name not in existing
            ]
            if not specs:
                raise ValueError(_("All fields of this ID3 frame are already shown."))
            with wx.SingleChoiceDialog(
                self, _("Optional field"), _("Add tag field"), [field_name(s.name) for s in specs]
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                spec = specs[dialog.Selection]
            added = make_node(spec.name, copy.deepcopy(spec.default))
        elif node.kind == "mapping":
            with wx.TextEntryDialog(self, _("Tag field name"), _("Add tag field")) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                name = dialog.Value.strip()
            if not name or any(c.name == name for c in node.children):
                raise ValueError(_("Enter a new, non-empty tag field name."))
            added = make_node(name, [""])
        elif node.kind in ("list", "tuple"):
            if len(self.roots) > 1 and node is self.roots[1]:
                added = make_node(
                    str(len(node.children) + 1),
                    dict(
                        type=3,
                        mime="image/jpeg",
                        desc="",
                        width=0,
                        height=0,
                        depth=0,
                        colors=0,
                        data=b"",
                    ),
                )
            elif node.children:
                added = copy.deepcopy(node.children[-1])
                added.name = str(len(node.children) + 1)
            else:
                with wx.SingleChoiceDialog(
                    self,
                    _("Value type"),
                    _("Add tag value"),
                    [
                        _("Text"),
                        _("Integer"),
                        _("Binary data"),
                        _("Pair of numbers"),
                        _("Pair of text values"),
                    ],
                ) as dialog:
                    if dialog.ShowModal() != wx.ID_OK:
                        return
                    value = ["", 0, b"", (0, 0), ["", ""]][dialog.Selection]
                added = make_node("1", value)
        else:
            raise ValueError(_("Select a field group or a list before adding a value."))
        node.children.append(added)
        self.refresh(added)

    def remove(self):
        node, owner = self.selection()
        if owner is None:
            return
        if owner.kind == "frame" and node.name in {s.name for s in owner.value._framespec}:
            raise ValueError(
                _("This ID3 field is required. Edit its value or remove the whole frame.")
            )
        if (
            wx.MessageBox(
                _("Remove the selected tag field or value?"),
                _("Edit audio tags"),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            == wx.YES
        ):
            owner.children.remove(node)
            self.refresh(owner)

    def export_binary(self):
        node, _owner = self.selection()
        if node is None or node.kind != "binary":
            raise ValueError(_("Select a binary tag value first."))
        with wx.FileDialog(
            self,
            _("Export binary tag value"),
            defaultFile="tag-data.bin",
            wildcard=_("Binary tag data") + "|*.bin",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                target = Path(dialog.Path)
                if target.suffix.casefold() != ".bin":
                    raise ValueError(_("Use the .bin extension for binary tag data."))
                atomic_write(target, node.value)

    def edit_v1(self):
        with V1Dialog(self, self.document.v1 if self.v1 is None else self.v1) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.v1 = dialog.raw

    def remove_v1(self):
        if (
            wx.MessageBox(
                _("Remove ID3v1 when saving? ID3v2 will be kept."),
                _("ID3v1 fields"),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            == wx.YES
        ):
            self.v1 = b""

    def accept(self, _event):
        try:
            node_value(self.document.tags)
        except (TypeError, ValueError) as exc:
            wx.MessageBox(str(exc), _("Invalid tag value"), wx.OK | wx.ICON_ERROR, self)
            return
        self.EndModal(wx.ID_OK)
