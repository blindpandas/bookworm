# coding: utf-8

import enum
import operator
import threading
from collections import namedtuple
from itertools import chain

import more_itertools
import wx
import wx.lib.sized_controls as sc

from bookworm import config
from bookworm.document.operations import SearchRequest
from bookworm.gui.components import (
    ColumnDefn,
    Dialog,
    DialogListCtrl,
    EnhancedSpinCtrl,
    EnumRadioBox,
    ImageViewControl,
    ImmutableObjectListView,
    PageRangeControl,
    SimpleDialog,
    make_sized_static_box,
)
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from bookworm.paths import images_path
from bookworm.reader import EBookReader
from bookworm.structured_text import (
    HEADING_LEVELS,
    SEMANTIC_ELEMENT_OUTPUT_OPTIONS,
    SemanticElementType,
)
from bookworm.utils import gui_thread_safe

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
        self.is_single_page_document = self.reader.document.is_single_page_document()
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
        if not self.is_single_page_document:
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
        if not self.is_single_page_document:
            wx.CallAfter(self.progressbar.SetValue, self.progressbar.GetValue() + 1)

    def addResult(self, result):
        if not self.IsShown():
            return
        with self.list_lock:
            self.addResultToList(result)
        if self.is_single_page_document:
            wx.CallAfter(self.progressbar.Pulse)

    def addResultToList(self, result):
        count = self.searchResultsListCtrl.ItemCount
        page_display_text = (
            str(result.page + 1) if not self.is_single_page_document else ""
        )
        index = self.searchResultsListCtrl.InsertItem(count, page_display_text)
        self.searchResultsListCtrl.SetItem(index, 1, result.excerpt)
        if self.reader.document.has_toc_tree():
            section_title = (
                result.section
                if not self.is_single_page_document
                else self.reader.document.get_section_at_position(result.position).title
            )
            self.searchResultsListCtrl.SetItem(index, 2, section_title)
        self.searchResultsListCtrl.SetItemData(index, result.position)


class SearchBookDialog(SimpleDialog):
    """Full text search dialog."""

    def addControls(self, parent):
        self.reader = self.parent.reader
        self.is_single_page_document = self.reader.document.is_single_page_document()
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
        from_page, to_page = self.pageRange.get_page_range()
        kwargs = {
            "from_page": from_page,
            "to_page": to_page,
        }
        if self.is_single_page_document:
            kwargs.update({"text_range": self.pageRange.get_text_range()})
        return SearchRequest(
            term=self.searchTermTextCtrl.GetValue().strip(),
            is_regex=self.isRegex.IsChecked(),
            case_sensitive=self.isCaseSensitive.IsChecked(),
            whole_word=self.isWholeWord.IsChecked(),
            **kwargs,
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


class ElementKind(enum.IntEnum):
    HEADING = SemanticElementType.HEADING
    LINK = SemanticElementType.LINK
    LIST = SemanticElementType.LIST
    TABLE = SemanticElementType.TABLE
    QUOTE = SemanticElementType.QUOTE

    @property
    def display(self):
        return _(SEMANTIC_ELEMENT_OUTPUT_OPTIONS[self.value][0])


class ElementListDialog(SimpleDialog):
    """Element list dialog."""

    def __init__(self, *args, view, reader, **kwargs):
        self.reader = reader
        self.view = view
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        self.elementTypeRadio = EnumRadioBox(
            parent,
            -1,
            label=_("Element Type"),
            choice_enum=ElementKind,
            majorDimension=0,
            style=wx.RA_SPECIFY_COLS,
        )
        self.elementListViewLabel = wx.StaticText(parent, -1, _("Elements"))
        self.elementListView = ImmutableObjectListView(
            parent,
            wx.ID_ANY,
            columns=[
                ColumnDefn(_("Name"), "left", 255, "name"),
            ],
        )
        self.Bind(
            wx.EVT_RADIOBOX, self.onElementTypeRadioSelected, self.elementTypeRadio
        )
        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self.onListItemActivated, self.elementListView
        )
        self.ElementInfo = namedtuple("ElementInfo", "type name  text_range")
        self.__element_Info_cache = {}
        self.populate_element_list(self.elementTypeRadio.GetSelectedValue())
        self.set_listview_label()

    def onElementTypeRadioSelected(self, event):
        self.set_listview_label()
        self.populate_element_list(event.GetEventObject().GetSelectedValue())

    def onListItemActivated(self, event):
        self.SetReturnCode(wx.ID_OK)
        self.Close()

    def set_listview_label(self):
        label = SEMANTIC_ELEMENT_OUTPUT_OPTIONS[
            self.elementTypeRadio.GetSelectedValue().value
        ][0]
        self.elementListViewLabel.SetLabelText(_(label))

    def populate_element_list(self, element_type):
        if (element_infos := self.__element_Info_cache.get(element_type)) is None:
            element_infos = list(self.iter_element_infos(element_type.value))
            if element_type is ElementKind.HEADING:
                for h_level in HEADING_LEVELS:
                    element_infos.extend(self.iter_element_infos(h_level))
            element_infos.sort(key=operator.attrgetter("text_range"))
        self.elementListView.set_objects(element_infos, set_focus=False)

    def iter_element_infos(self, element_type):
        ElementInfo = self.ElementInfo
        text_whole_line = SEMANTIC_ELEMENT_OUTPUT_OPTIONS[element_type][1]
        for text_range in self.reader.iter_semantic_ranges_for_elements_of_type(
            element_type
        ):
            if text_whole_line:
                name = self.view.get_text_by_range(
                    *self.view.get_containing_line(text_range[0])
                )
            else:
                name = self.view.get_text_by_range(*text_range)
            yield ElementInfo(element_type, name.strip(), text_range)

    def ShowModal(self):
        super().ShowModal()
        return self.elementListView.get_selected()


class DocumentInfoDialog(SimpleDialog):
    def __init__(
        self,
        *args,
        document_info,
        view=None,
        offer_open_action=False,
        open_in_a_new_instance=False,
        **kwargs,
    ):
        self.document_info = document_info
        self.view = view
        self.offer_open_action = offer_open_action
        self.open_in_a_new_instance = open_in_a_new_instance
        # Translators: title of a dialog
        kwargs.setdefault("title", _("Document Info"))
        kwargs.setdefault("size", (750, 750))
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        parent.SetSizerType("horizontal")
        parent.SetSizerProps(expand=True)
        if (cover_image := self.get_cover_image()) is not None:
            image_view = ImageViewControl(parent, -1)
            image_view.RenderImageIO(cover_image)
            parent.GetSizer().AddSpacer(25)
        rh_panel = sc.SizedPanel(parent, -1)
        rh_panel.SetSizerType("vertical")
        rh_panel.SetSizerProps(expand=True, hgrow=100)
        title_text_ctrl = self.create_info_field(
            rh_panel, label=_("Title"), value=self.document_info.title
        )
        title_text_style = title_text_ctrl.GetDefaultStyle()
        title_text_style_font_size = title_text_style.GetFontSize()
        title_text_style.SetFontSize(
            round(title_text_style_font_size + (title_text_style_font_size * 0.5))
        )
        title_text_style.SetFontWeight(wx.FONTWEIGHT_EXTRABOLD)
        title_text_ctrl.SetStyle(0, title_text_ctrl.GetLastPosition(), title_text_style)
        if authors := self.document_info.authors:
            if type(authors) is not str:
                label = _("Authors")
                authors = "\n".join(a.strip() for a in authors)
            else:
                label = _("Author")
            self.create_info_field(rh_panel, label=label, value=authors)
        if description := self.document_info.description:
            desc_text_ctrl = self.create_info_field(
                rh_panel, label=_("Description"), value=description
            )
            desc_text_ctrl_style = desc_text_ctrl.GetDefaultStyle()
            desc_text_ctrl_style.SetFontWeight(wx.FONTWEIGHT_BOLD)
            desc_text_ctrl.SetStyle(
                0, desc_text_ctrl.GetLastPosition(), desc_text_ctrl_style
            )
        if num_sections := self.document_info.number_of_sections:
            self.create_info_field(
                rh_panel, label=_("Number of Sections"), value=str(num_sections)
            )
        if num_pages := self.document_info.number_of_pages:
            self.create_info_field(
                rh_panel, label=_("Number of Pages"), value=str(num_pages)
            )
        self.create_info_field(
            rh_panel, label=_("Language"), value=self.document_info.language.native_name
        )
        if publisher := self.document_info.publisher:
            self.create_info_field(rh_panel, label=_("Publisher"), value=publisher)
        if creation_date := self.document_info.creation_date:
            self.create_info_field(rh_panel, label=_("Created at"), value=creation_date)
        if pub_date := self.document_info.publication_date:
            self.create_info_field(
                rh_panel, label=_("Publication Date"), value=pub_date
            )
        if self.offer_open_action:
            # Translators: the label of the close button in a dialog
            openBtn = wx.Button(rh_panel, wx.ID_OPEN, _("&Open"))
            openBtn.SetSizerProps(halign="center")
            self.Bind(wx.EVT_BUTTON, self.onOpenDocument, openBtn)
        parent.SetMinSize((900, -1))
        parent.Layout()
        parent.Fit()

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of the close button in a dialog
        closeBtn = wx.Button(self, wx.ID_CANCEL, _("&Close"))
        btnsizer.AddButton(closeBtn)
        btnsizer.Realize()
        return btnsizer

    def onOpenDocument(self, event):
        self.Close()
        if self.open_in_a_new_instance:
            EBookReader.open_document_in_a_new_instance(self.document_info.uri)
        else:
            self.view.open_uri(self.document_info.uri)

    def get_cover_image(self):
        if cover_image := self.document_info.cover_image:
            return cover_image.make_thumbnail(512, 512)
        return ImageIO.from_filename(
            images_path("generic_document.png")
        ).make_thumbnail(270, 270)

    def create_info_field(self, parent, label, value):
        wx.StaticText(parent, -1, label)
        text_ctrl = wx.TextCtrl(
            parent,
            -1,
            value=value,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
        )
        text_ctrl.SetSizerProps(expand=True)
        text_ctrl.SetMinSize((500, -1))
        return text_ctrl
