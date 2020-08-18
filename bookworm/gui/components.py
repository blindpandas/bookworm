# coding: utf-8

import System
import contextlib
import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.sized_controls as sc
import wx.lib.newevent
from collections.abc import Container
from dataclasses import dataclass
from itertools import chain
import bookworm.typehints as t
from bookworm.logger import logger


log = logger.getChild(__name__)


def make_sized_static_box(parent, title):
    stbx = sc.SizedStaticBox(parent, -1, title)
    stbx.SetSizerProp("expand", True)
    stbx.Sizer.AddSpacer(25)
    return stbx


@dataclass
class SelectionRange(Container):
    """Represents a text range in an edit control."""

    start: int
    end: int

    def __contains__(self, x):
        return self.start <= x <= self.end

    def __iter__(self):
        return iter((self.start, self.end))


class CustomContextMenuTextCtrl(wx.TextCtrl):
    """
    Provides a unified method to capture context menu requests in TextCtrl's.
    Also contains some work arounds.
    """

    ContextMenuEvent, EVT_CONTEXTMENU_REQUESTED = wx.lib.newevent.NewCommandEvent()

    def TryBefore(self, event):
        evtType = event.GetEventType()
        if evtType == wx.EVT_CONTEXT_MENU.typeId:
            wx.PostEvent(self, self.ContextMenuEvent(self.GetId(), fromMouse=False))
            return True
        elif evtType == wx.EVT_RIGHT_UP.typeId:
            wx.PostEvent(self, self.ContextMenuEvent(self.GetId(), fromMouse=True))
            return True
        elif evtType == wx.EVT_KEY_UP.typeId and (
            event.GetKeyCode() == wx.WXK_WINDOWS_MENU
        ):
            # Prevent duplication
            return True
        return super().TryBefore(event)


class EnhancedSpinCtrl(wx.SpinCtrl):
    """
    Select the content of the ctrl when focused to make editing more easier.
    Inspired by a simular code in NVDA's gui package.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_SET_FOCUS, self.onFocus, self)

    def onFocus(self, event):
        event.Skip()
        length = len(str(self.GetValue()))
        self.SetSelection(0, length)


class PageRangeControl(sc.SizedPanel):
    def __init__(self, parent, document):
        parent = parent
        self.doc = document
        num_pages = len(self.doc)

        # Translators: the title of a group of controls in the search dialog
        rangeBox = make_sized_static_box(parent, _("Search Range"))
        # Translators: the label of a radio button in the search dialog
        self.hasPage = wx.RadioButton(rangeBox, -1, _("Page Range"), style=wx.RB_GROUP)
        fromToPagePanel = make_sized_static_box(rangeBox, "")
        fromToPagePanel.SetSizerProps(expand=True)
        fromToPagePanel.SetSizerType("horizontal")
        # Translators: the label of an edit field in the search dialog
        # to enter the page from which the search will start
        fpage_label = wx.StaticText(fromToPagePanel, -1, _("From:"))
        self.fromPage = EnhancedSpinCtrl(
            fromToPagePanel, -1, min=1, max=num_pages, value="1"
        )
        # Translators: the label of an edit field in the search dialog
        # to enter the page number at which the search will stop
        tpage_label = wx.StaticText(fromToPagePanel, -1, _("To:"))
        self.toPage = EnhancedSpinCtrl(
            fromToPagePanel, -1, min=1, max=num_pages, value=str(num_pages)
        )
        # Translators: the label of a radio button in the search dialog
        self.hasSection = wx.RadioButton(rangeBox, -1, _("Specific section"))
        # Translators: the label of a combobox in the search dialog
        # to choose the section to which the search will be confined
        sec_label = wx.StaticText(rangeBox, -1, _("Select section:"))
        self.sectionChoice = wx.Choice(
            rangeBox, -1, choices=[sect.title for sect in self.doc.toc_tree]
        )
        self.page_controls = (fpage_label, tpage_label, self.fromPage, self.toPage)
        self.sect_controls = (sec_label, self.sectionChoice)
        for ctrl in chain(self.page_controls, self.sect_controls):
            ctrl.Enable(False)
        for radio in (self.hasPage, self.hasSection):
            radio.SetValue(0)
            parent.Bind(wx.EVT_RADIOBUTTON, self.onRangeTypeChange, radio)

    def onRangeTypeChange(self, event):
        radio = event.GetEventObject()
        if radio == self.hasPage:
            controls = self.page_controls
        else:
            controls = self.sect_controls
        for ctrl in chain(self.page_controls, self.sect_controls):
            ctrl.Enable(ctrl in controls)

    def get_range(self):
        if self.hasSection.GetValue():
            selected_section = self.sectionChoice.GetSelection()
            if selected_section != wx.NOT_FOUND:
                pager = self.doc.toc_tree[selected_section].pager
                from_page = pager.first
                to_page = pager.last
        else:
            from_page = self.fromPage.GetValue() - 1
            to_page = self.toPage.GetValue() - 1
        return from_page, to_page


class DialogListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(
        self,
        parent,
        id,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.BORDER_SUNKEN
        | wx.LC_SINGLE_SEL
        | wx.LC_REPORT
        | wx.LC_EDIT_LABELS
        | wx.LC_VRULES,
    ):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class Dialog(wx.Dialog):
    """Base dialog for `Bookworm` GUI dialogs."""

    def __init__(self, parent, title, size=(450, 450), style=wx.DEFAULT_DIALOG_STYLE):
        super().__init__(parent, title=title, style=style)
        self.parent = parent

        panel = wx.Panel(self, -1, size=size)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.addControls(sizer, panel)
        line = wx.StaticLine(panel, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.RIGHT | wx.TOP, 10)
        buttonsSizer = self.getButtons(panel)
        if buttonsSizer:
            sizer.Add(buttonsSizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(sizer)
        panel.Layout()
        sizer.Fit(panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 2, wx.EXPAND | wx.ALL, 15)
        self.SetSizer(sizer)
        self.Fit()
        self.Center()

    def addControls(self, sizer):
        raise NotImplementedError

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the lable of the OK button in a dialog
        okBtn = wx.Button(parent, wx.ID_OK, _("OK"))
        okBtn.SetDefault()
        # Translators: the lable of the cancel button in a dialog
        cancelBtn = wx.Button(parent, wx.ID_CANCEL, _("Cancel"))
        for btn in (okBtn, cancelBtn):
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        return btnsizer


class SimpleDialog(sc.SizedDialog):
    """Basic dialog for simple  GUI forms."""

    def __init__(self, parent, title, style=wx.DEFAULT_DIALOG_STYLE, **kwargs):
        super().__init__(parent, title=title, style=style, **kwargs)
        self.parent = parent

        panel = self.GetContentsPane()
        self.addControls(panel)
        buttonsSizer = self.getButtons(panel)
        if buttonsSizer:
            self.SetButtonSizer(buttonsSizer)

        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Center(wx.BOTH)

    def SetButtonSizer(self, sizer):
        bottomSizer = wx.BoxSizer(wx.VERTICAL)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        bottomSizer.Add(line, 0, wx.TOP | wx.EXPAND, 15)
        bottomSizer.Add(sizer, 0, wx.EXPAND | wx.ALL, 10)
        super().SetButtonSizer(bottomSizer)

    def addControls(self, parent):
        raise NotImplementedError

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the lable of the OK button in a dialog
        okBtn = wx.Button(self, wx.ID_OK, _("OK"))
        okBtn.SetDefault()
        # Translators: the lable of the cancel button in a dialog
        cancelBtn = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        for btn in (okBtn, cancelBtn):
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        return btnsizer


class SnakDialog(SimpleDialog):
    """A Toast style notification  dialog for showing a simple message without a title."""

    def __init__(self, message, *args, dismiss_callback=None, **kwargs):
        self.message = message
        self.dismiss_callback = dismiss_callback
        super().__init__(*args, title="", style=0, **kwargs)

    def addControls(self, parent):
        self.staticMessage = wx.StaticText(parent, -1, self.message)
        self.staticMessage.SetCanFocus(True)
        self.staticMessage.SetFocusFromKbd()
        self.Bind(wx.EVT_CLOSE, self.onClose, self)
        self.staticMessage.Bind(wx.EVT_KEY_UP, self.onKeyUp, self.staticMessage)
        self.CenterOnParent()

    def onClose(self, event):
        if event.CanVeto():
            if self.dismiss_callback is not None:
                should_close = self.dismiss_callback()
                if should_close:
                    self.Hide()
                    return
            event.Veto()
        else:
            self.Destroy()

    def onKeyUp(self, event):
        event.Skip()
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()

    def getButtons(self, parent):
        return


@dataclass
class ColumnDefn:
    title: str
    alignment: str
    width: int
    string_converter: t.Union[t.Callable[[t.Any], str], str]

    _ALIGNMENT_FLAGS = {
        "left": wx.LIST_FORMAT_LEFT,
        "center": wx.LIST_FORMAT_CENTRE,
        "right": wx.LIST_FORMAT_RIGHT,
    }

    @property
    def alignment_flag(self):
        flag = self._ALIGNMENT_FLAGS.get(self.alignment)
        if flag is not None:
            return flag
        raise ValueError(f"Unknown alignment directive {self.alignment}")


ObjectCollection = t.Iterable[t.Any]
ColumnSpecs = t.Iterable[ColumnDefn]


class ImmutableObjectListView(DialogListCtrl):
    """An immutable  list view that deals with objects rather than strings."""

    def __init__(
        self, *args, columns: ColumnSpecs = (), objects: ObjectCollection = (), **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._objects = None
        self._columns = None
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self.onDeleteItem, self)
        self.Bind(wx.EVT_LIST_DELETE_ALL_ITEMS, self.onDeleteAllItems, self)
        self.Bind(wx.EVT_LIST_INSERT_ITEM, self.onInsertItem, self)
        self.__is_modifying = False
        self.set_columns(columns)
        self.set_objects(objects)

    @contextlib.contextmanager
    def __unsafe_modify(self):
        self.__is_modifying = True
        yield
        self.__is_modifying = False

    def set_columns(self, columns):
        self.ClearAll()
        self._columns = columns
        for col in self._columns:
            self.AppendColumn(col.title, format=col.alignment_flag, width=col.width)
        for i in range(len(columns)):
            self.SetColumnWidth(i, 100)

    def set_objects(self, objects: ObjectCollection, focus_item: int = 0):
        """Clear the list view and insert the objects."""
        self._objects = objects
        self.set_columns(self._columns)
        string_converters = [c.string_converter for c in self._columns]
        with self.__unsafe_modify():
            for obj in self._objects:
                col_labels = []
                for to_str in string_converters:
                    col_labels.append(
                        getattr(obj, to_str) if not callable(to_str) else to_str(obj)
                    )
                self.Append(col_labels)
        self.set_focused_item(focus_item)

    def get_selected(self) -> t.Optional[t.Any]:
        """Return the currently selected object or None."""
        idx = self.GetFocusedItem()
        if idx != wx.NOT_FOUND:
            return self._objects[idx]

    def set_focused_item(self, idx: int):
        if idx >= self.ItemCount:
            return
        self.SetFocus()
        self.EnsureVisible(idx)
        self.Select(idx)
        self.SetItemState(idx, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)

    def prevent_mutations(self):
        if not self.__is_modifying:
            raise RuntimeError(
                "List is immutable. Use 'ImmutableObjectListView.set_objects' instead"
            )

    def onDeleteItem(self, event):
        self.prevent_mutations()

    def onDeleteAllItems(self, event):
        ...

    def onInsertItem(self, event):
        self.prevent_mutations()
