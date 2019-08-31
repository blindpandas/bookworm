# coding: utf-8

import wx
import wx.lib.scrolledpanel as scrolled
import fitz
from itertools import chain
from bookworm import config
from bookworm import speech
from bookworm.speech.enumerations import SynthState
from bookworm.document_formats import SearchRequest
from bookworm.signals import reader_page_changed
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from ..components import Dialog, SimpleDialog, DialogListCtrl, EnhancedSpinCtrl
from ..preferences_dialog import SpeechPanel, ReconciliationStrategies
from .navigation import NavigationProvider


log = logger.getChild(__name__)


class SearchResultsDialog(Dialog):
    """Search Results."""

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
        sizer.Add(
            self.searchResultsListCtrl, 1, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, 10
        )
        sizer.Add(pbarlabel, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(self.progressbar, 0, wx.EXPAND | wx.ALL, 10)
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
            page = self.searchResultsListCtrl.GetItemText(idx)
            pos = self.searchResultsListCtrl.GetItemData(idx)
            self.Close()
            self.Destroy()
            self.parent.highlight_search_result(int(page) - 1, pos)
            self.parent._last_search_index = idx

    def addResult(self, page, snip, section, pos):
        count = self.searchResultsListCtrl.ItemCount
        index = self.searchResultsListCtrl.InsertItem(count, str(page + 1))
        self.searchResultsListCtrl.SetItem(index, 1, snip)
        self.searchResultsListCtrl.SetItem(index, 2, section)
        self.searchResultsListCtrl.SetItemData(index, pos)


class SearchBookDialog(Dialog):
    """Full text search dialog."""

    def addControls(self, sizer, parent):
        self.reader = self.parent.reader
        num_pages = len(self.parent.reader.document)
        recent_terms = config.conf["history"]["recent_terms"]
        # Translators: the label of an edit field in the search dialog
        st_label = wx.StaticText(parent, -1, _("Search term:"))
        self.searchTermTextCtrl = wx.ComboBox(
            parent, -1, choices=recent_terms, style=wx.CB_DROPDOWN
        )
        # Translators: the label of a checkbox
        self.isCaseSensitive = wx.CheckBox(parent, -1, _("Case sensitive"))
        # Translators: the label of a checkbox
        self.isWholeWord = wx.CheckBox(parent, -1, _("Match whole word only"))
        # Translators: the title of a group of controls in the search dialog
        rbTitle = wx.StaticBox(parent, -1, _("Search Range"))
        searchRangeBox = wx.StaticBoxSizer(rbTitle, wx.VERTICAL)
        # Translators: the label of a radio button in the search dialog
        self.hasPage = wx.RadioButton(parent, -1, _("Page Range"), style=wx.RB_GROUP)
        rsizer = wx.BoxSizer(wx.HORIZONTAL)
        # Translators: the label of an edit field in the search dialog
        # to enter the page from which the search will start
        fpage_label = wx.StaticText(parent, -1, _("From:"))
        self.fromPage = EnhancedSpinCtrl(parent, -1, min=1, max=num_pages, value="1")
        # Translators: the label of an edit field in the search dialog
        # to enter the page number at which the search will stop
        tpage_label = wx.StaticText(parent, -1, _("To:"))
        self.toPage = EnhancedSpinCtrl(
            parent, -1, min=1, max=num_pages, value=str(num_pages)
        )
        rsizer.AddMany(
            [
                (fpage_label, 0, wx.ALL, 5),
                (self.fromPage, 1, wx.ALL, 5),
                (tpage_label, 0, wx.ALL, 5),
                (self.toPage, 1, wx.ALL, 5),
            ]
        )
        # Translators: the label of a radio button in the search dialog
        self.hasSection = wx.RadioButton(parent, -1, _("Specific section"))
        # Translators: the label of a combobox in the search dialog
        # to choose the section to which the search will be confined
        sec_label = wx.StaticText(parent, -1, _("Select section:"))
        self.sectionChoice = wx.Choice(
            parent, -1, choices=[sect.title for sect in self.reader.document.toc_tree]
        )
        secsizer = wx.BoxSizer(wx.HORIZONTAL)
        secsizer.AddMany(
            [(sec_label, 0, wx.ALL, 5), (self.sectionChoice, 1, wx.ALL, 5)]
        )
        searchRangeBox.Add(self.hasPage, 0, wx.ALL, 10)
        searchRangeBox.Add(rsizer, wx.EXPAND | wx.ALL, 10)
        searchRangeBox.Add(self.hasSection, 0, wx.ALL, 10)
        searchRangeBox.Add(secsizer, wx.EXPAND | wx.ALL, 10)
        sizer.Add(st_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer.Add(self.searchTermTextCtrl, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.isCaseSensitive, 0, wx.TOP | wx.BOTTOM, 10)
        sizer.Add(self.isWholeWord, 0, wx.BOTTOM, 10)
        sizer.Add(searchRangeBox, 0, wx.ALL, 10)
        self.page_controls = (fpage_label, tpage_label, self.fromPage, self.toPage)
        self.sect_controls = (sec_label, self.sectionChoice)
        for ctrl in chain(self.page_controls, self.sect_controls):
            ctrl.Enable(False)
        for radio in (self.hasPage, self.hasSection):
            radio.SetValue(0)
            self.Bind(wx.EVT_RADIOBUTTON, self.onSearchRange, radio)

    def GetValue(self):
        if self.hasSection.GetValue():
            selected_section = self.sectionChoice.GetSelection()
            if selected_section != wx.NOT_FOUND:
                pager = self.reader.document.toc_tree[selected_section].pager
                from_page = pager.first
                to_page = pager.last
        else:
            from_page = self.fromPage.GetValue() - 1
            to_page = self.toPage.GetValue() - 1
        return SearchRequest(
            term=self.searchTermTextCtrl.GetValue().strip(),
            case_sensitive=self.isCaseSensitive.IsChecked(),
            whole_word=self.isWholeWord.IsChecked(),
            from_page=from_page,
            to_page=to_page,
        )

    def onSearchRange(self, event):
        radio = event.GetEventObject()
        if radio == self.hasPage:
            controls = self.page_controls
        else:
            controls = self.sect_controls
        for ctrl in chain(self.page_controls, self.sect_controls):
            ctrl.Enable(ctrl in controls)


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


class ViewPageAsImageDialog(wx.Dialog):
    """Show the page rendered as an image."""

    def __init__(self, parent, title, size=(450, 450), style=wx.DEFAULT_DIALOG_STYLE):
        super().__init__(parent, title=title, style=style)
        self.parent = parent
        self.reader = self.parent.reader
        # Zoom support
        self.scaling_factor = 0.2
        self._zoom_factor = 1
        self.scroll_rate = 30
        # Translators: the label of the image of a page in a dialog to render the current page
        panel = self.scroll = scrolled.ScrolledPanel(self, -1, name=_("Page"))
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.imageCtrl = wx.StaticBitmap(panel)
        sizer.Add(self.imageCtrl, 1, wx.CENTER | wx.BOTH)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        panel.Layout()
        self.setDialogImage()
        NavigationProvider(
            ctrl=panel,
            reader=self.reader,
            callback_func=self.setDialogImage,
            zoom_callback=self.set_zoom,
        )
        panel.Bind(wx.EVT_KEY_UP, self.onKeyUp, panel)
        panel.SetupScrolling(rate_x=self.scroll_rate, rate_y=self.scroll_rate)
        self._currently_rendered_page = self.reader.current_page
        reader_page_changed.connect(self.onPageChange, sender=self.reader)

    @gui_thread_safe
    def onPageChange(self, sender, current, prev):
        if self._currently_rendered_page != current:
            self.setDialogImage()

    def set_zoom(self, val):
        if val == 0:
            self.zoom_factor = 1
        else:
            self.zoom_factor += val * self.scaling_factor

    @property
    def zoom_factor(self):
        return self._zoom_factor

    @zoom_factor.setter
    def zoom_factor(self, value):
        if (value < 1.0) or (value > 10.0):
            return
        self._zoom_factor = value
        self.setDialogImage()
        self.scroll.SetupScrolling(rate_x=self.scroll_rate, rate_y=self.scroll_rate)
        # Translators: a message announced to the user when the zoom factor changes
        speech.announce(
            _("Zoom is at {factor} percent").format(factor=int(value * 100))
        )

    def setDialogImage(self):
        bmp, size = self.getPageImage()
        self.imageCtrl.SetBitmap(bmp)
        self.imageCtrl.SetSize(size)
        self._currently_rendered_page = self.reader.current_page

    def getPageImage(self):
        page = self.reader.document[self.reader.current_page]
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.getPixmap(matrix=mat, alpha=True)
        bmp = wx.Bitmap.FromBufferRGBA(pix.width, pix.height, pix.samples)
        size = (bmp.GetWidth(), bmp.GetHeight())
        return bmp, size

    def onKeyUp(self, event):
        event.Skip()
        code = event.GetKeyCode()
        if code == wx.WXK_ESCAPE:
            self.Close()
            self.Destroy()


class VoiceProfileEditorDialog(SimpleDialog):
    """Create and edit voice profiles."""

    def __init__(self, parent, profile_name, profile):
        self.profile = profile
        # Translators: the title of a dialog to edit a voice profile
        title = _("Voice Profile: {profile}").format(profile=profile_name)
        super().__init__(parent, title)

    def addControls(self, parent):
        cPanel = self.spPanel = SpeechPanel(parent, config_object=self.profile)
        self.Bind(wx.EVT_BUTTON, self.onSubmit, id=wx.ID_OK)
        cPanel.reconcile()
        cPanel.Children[0].Children[1].SetFocus()

    def onSubmit(self, event):
        self.spPanel.reconcile(ReconciliationStrategies.save)
        self.Close()


class VoiceProfileDialog(SimpleDialog):
    """Voice Profiles."""

    def addControls(self, parent):
        self.reader = self.parent.reader

        # Translators: the label of a combobox to select a voice profile
        label = wx.StaticText(parent, -1, _("Select Voice Profile:"))
        self.voiceProfilesChoice = wx.Choice(parent, -1, choices=[])
        self.voiceProfilesChoice.SetSizerProps(expand=True)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        # Translators: the label of a button to activate a voice profile
        ab = wx.Button(self, wx.ID_DEFAULT, _("&Activate"))
        # Translators: the label of a button to edit a voice profile
        eb = wx.Button(self, wx.ID_EDIT, _("&Edit..."))
        # Translators: the label of a button to remove a voice profile
        rb = wx.Button(self, wx.ID_REMOVE, _("&Remove"))
        # Translators: the label of a button to create a new voice profile
        nb = wx.Button(self, wx.ID_NEW, _("&New Profile..."))
        for c in (ab, eb, rb, nb):
            btnSizer.Add(c, 0, wx.ALL, 10)
        # Translators: the label of a button to close the dialog
        btnSizer.Add(wx.Button(self, wx.ID_CANCEL, _("&Close")), 0, wx.ALL, 10)
        self.SetButtonSizer(btnSizer)
        ab.SetDefault()

        # Event handling
        self.Bind(wx.EVT_BUTTON, self.onActivate, id=wx.ID_DEFAULT)
        self.Bind(wx.EVT_BUTTON, self.onEdit, id=wx.ID_EDIT)
        self.Bind(wx.EVT_BUTTON, self.onRemove, id=wx.ID_REMOVE)
        self.Bind(wx.EVT_BUTTON, self.onNew, id=wx.ID_NEW)

        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Center(wx.BOTH)
        self.refresh_profile_list()

    def refresh_profile_list(self):
        self.voiceProfilesChoice.Clear()
        config.conf.list_voice_profiles()
        profiles = list(sorted(config.conf.profiles.keys()))
        self.voiceProfilesChoice.SetFocus()
        for btn in (wx.ID_EDIT, wx.ID_DEFAULT, wx.ID_REMOVE):
            self.FindWindowById(btn).Enable(bool(profiles))
        if not profiles:
            return
        sel = 0
        active_profile = config.conf.active_profile
        for i, profile in enumerate(profiles):
            label = _(profile)
            if active_profile and active_profile["name"] == profile:
                # Translators: the entry of the active voice profile in the voice profiles list
                label = _("{profile} (active)").format(profile=label)
                sel = i
            self.voiceProfilesChoice.Append(label, profile)
        self.voiceProfilesChoice.SetSelection(sel)

    @property
    def selected_profile(self):
        selection = self.voiceProfilesChoice.GetSelection()
        if selection != wx.NOT_FOUND:
            return self.voiceProfilesChoice.GetClientData(selection)

    def onActivate(self, event):
        profile_name = self.selected_profile
        if profile_name is None:
            return wx.Bell()
        active_profile = config.conf.active_profile
        if active_profile and profile_name == active_profile["name"]:
            self.Close()
            return wx.Bell()
        self.activate_profile(profile_name)
        self.Close()

    def activate_profile(self, profile_name):
        if profile_name not in config.conf.profiles:
            return
        config.conf.active_profile = config.conf.profiles[profile_name]
        if self.reader.ready:
            self.reader.tts.configure_engine()
        self.Parent.menuBar.FindItemById(wx.ID_REVERT).Enable(True)

    def onEdit(self, event):
        profile_name = self.selected_profile
        profile = config.conf.profiles.get(profile_name)
        if not profile:
            return wx.Bell()
        with VoiceProfileEditorDialog(
            self, profile_name=profile_name, profile=profile
        ) as dlg:
            dlg.ShowModal()
        if (
            config.conf.active_profile
            and profile_name == config.conf.active_profile["name"]
        ):
            self.activate_profile(profile_name)

    def onNew(self, event):
        profile_name = wx.GetTextFromUser(
            # Translators: the label of an edit field to enter the voice profile name
            _("Profile Name:"),
            # Translators: the title of a dialog to enter the name of a new voice profile
            _("New Voice Profile"),
            parent=self,
        )
        if not profile_name.strip():
            return wx.Bell()
        profile_name = profile_name.title()
        try:
            profile = config.conf.create_voice_profile(profile_name)
        except ValueError:
            wx.MessageBox(
                # Translators: the content of a message notifying the user
                # user of the existance of a voice profile with the same name
                _(
                    "A voice profile with the same name already exists. Please select another name."
                ),
                # Translators: the title of a message telling the user that an error has occurred
                _("Error"),
                style=wx.ICON_WARNING,
            )
            return self.onNew(event)
        with VoiceProfileEditorDialog(
            self, profile_name=profile_name, profile=profile
        ) as dlg:
            dlg.ShowModal()
        profile.write()
        self.refresh_profile_list()

    def onRemove(self, event):
        profile_name = self.selected_profile
        if profile_name not in config.conf.profiles:
            return wx.Bell()
        elif (
            config.conf.active_profile
            and config.conf.active_profile["name"] == profile_name
        ):
            wx.MessageBox(
                # Translators: the content of a message telling the user that the voice
                # profile he is removing is the active one
                _(
                    "Voice profile {profile} is the active profile.\n"
                    "Please deactivate it first by clicking 'Deactivate Active Voice Profile` "
                    "menu item from the speech menu."
                ).format(profile=profile_name),
                # Translators: the title of a message telling the user that
                # it is not possible to remove this voice profile
                _("Cannot Remove Profile"),
                style=wx.ICON_INFORMATION,
            )
            return
        msg = wx.MessageBox(
            # Translators: the title of a message to confirm the removal of the voice profile
            _(
                "Are you sure you want to remove voice profile {profile}?\n"
                "This cannot be undone."
            ).format(profile=profile_name),
            # Translators: the title of a message to confirm the removal of a voice profile
            _("Remove Voice Profile?"),
            parent=self,
            style=wx.YES | wx.NO | wx.ICON_QUESTION,
        )
        if msg == wx.YES:
            config.conf.delete_voice_profile(profile_name)
            self.refresh_profile_list()

    def getButtons(self, parent):
        return
