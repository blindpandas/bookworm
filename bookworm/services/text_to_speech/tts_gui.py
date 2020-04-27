# coding: utf-8


import wx
from bookworm.speech.enumerations import SynthState
from bookworm.gui.components import SimpleDialog
from bookworm.gui.preferences_dialog import SettingsPanel, ReconciliationStrategies



# Dialogs
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
            self.reader.tts.initialize_engine()
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


class SpeechEngineSelector(SimpleDialog):
    """A dialog to select a speech engine."""

    def __init__(self, choices, init_selection, *args, **kwargs):
        self.choices = choices
        self.init_selection = init_selection
        self._return_value = wx.ID_CANCEL
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        # Translators: the label of a combobox
        label = wx.StaticText(parent, -1, _("Select Speech Engine:"))
        self.engineChoice = wx.Choice(parent, -1, choices=self.choices)
        self.engineChoice.SetSizerProps(expand=True)
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.engineChoice.SetSelection(self.init_selection)
        self.GetValue = lambda: self.engineChoice.GetSelection()

    def onOK(self, event):
        self._return_value = wx.ID_OK
        self.Close()

    def ShowModal(self):
        super().ShowModal()
        return self._return_value

# Setting Panel

class SpeechPanel(SettingsPanel):
    config_section = "speech"

    def addControls(self):
        # Translators: the label of a group of controls in the
        # speech settings page related to voice selection
        voiceBox = self.make_static_box(_("Voice"))
        # voiceBox.SetSizerType("form")
        # Translators: the label of a combobox containing a list of tts engines
        wx.StaticText(voiceBox, -1, _("Speech Engine:"))
        self.engineInfoText = wx.TextCtrl(
            voiceBox, -1, style=wx.TE_READONLY | wx.TE_MULTILINE
        )
        # Translators: the label of a button that opens a dialog to change the speech engine
        self.changeEngineBtn = wx.Button(voiceBox, -1, _("Change..."))
        # Translators: the label of a combobox containing a list of tts voices
        wx.StaticText(voiceBox, -1, _("Select Voice:"))
        self.voice = wx.Choice(voiceBox, -1)
        # Translators: the label of the speech rate slider
        wx.StaticText(voiceBox, -1, _("Speech Rate:"))
        rt = wx.Slider(voiceBox, -1, minValue=0, maxValue=100, name="speech.rate")
        rt.SetPageSize(DEFAULT_STEP_SIZE)
        # Translators: the label of the speech volume slider
        wx.StaticText(voiceBox, -1, _("Speech Volume:"))
        vol = wx.Slider(voiceBox, -1, minValue=0, maxValue=100, name="speech.volume")
        vol.SetPageSize(DEFAULT_STEP_SIZE)
        # Translators: the label of a group of controls in the speech
        # settings page related to speech pauses
        pausesBox = self.make_static_box(_("Pauses"))
        # pausesBox.SetSizerType("form")
        # Translators: the label of an edit field
        wx.StaticText(pausesBox, -1, _("Additional Pause At Sentence End (Ms)"))
        sp = EnhancedSpinCtrl(
            pausesBox, -1, min=0, max=PARAGRAPH_PAUSE_MAX, name="speech.sentence_pause"
        )
        # Translators: the label of an edit field
        wx.StaticText(pausesBox, -1, _("Additional Pause At Paragraph End (Ms)"))
        pp = EnhancedSpinCtrl(
            pausesBox, -1, min=0, max=PARAGRAPH_PAUSE_MAX, name="speech.paragraph_pause"
        )
        # Translators: the label of an edit field
        wx.StaticText(pausesBox, -1, _("End of Page Pause (ms)"))
        eop = EnhancedSpinCtrl(
            pausesBox,
            -1,
            min=0,
            max=END_OF_PAGE_PAUSE_MAX,
            name="speech.end_of_page_pause",
        )
        # Translators: the label of an edit field
        wx.StaticText(pausesBox, -1, _("End of Section Pause (ms)"))
        eos = EnhancedSpinCtrl(
            pausesBox,
            -1,
            min=0,
            max=END_OF_SECTION_PAUSE_MAX,
            name="speech.end_of_section_pause",
        )
        for ctrl in (sp, pp, eop, eos, self.engineInfoText):
            ctrl.SetSizerProps(expand=True)
        self.changeEngineBtn.Bind(
            wx.EVT_BUTTON, self.OnChoosEngine, self.changeEngineBtn
        )
        self.current_engine = None
        self.configure_with_engine()
        self.changeEngineBtn.Enable(len(SpeechProvider.speech_engines) > 1)

    def configure_with_engine(self, engine_name=""):
        if (self.current_engine is not None) and (
            engine_name == self.current_engine.name
        ):
            return
        engine_name = engine_name or self.config["engine"]
        self.current_engine = SpeechProvider.get_engine(engine_name)
        self.engineInfoText.SetValue(_(self.current_engine.display_name))
        self.voices = self.current_engine().get_voices()
        self.voice.Clear()
        self.voice.Append([v.display_name for v in self.voices])
        self.reconcile()

    def OnChoosEngine(self, event):
        from .book_viewer.core_dialogs import SpeechEngineSelector

        current_engine_index = 0
        for (index, e) in enumerate(SpeechProvider.speech_engines):
            if e.name == self.current_engine.name:
                current_engine_index = index
        dlg = SpeechEngineSelector(
            [_(e.display_name) for e in SpeechProvider.speech_engines],
            current_engine_index,
            parent=self.Parent,
            title=_("Speech Engine"),
        )
        with dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.configure_with_engine(
                    SpeechProvider.speech_engines[dlg.GetValue()].name
                )

    def reconcile(self, strategy=ReconciliationStrategies.load):
        if strategy is ReconciliationStrategies.load:
            configured_voice = self.config["voice"]
            pos = 0
            for idx, vinfo in enumerate(self.voices):
                if vinfo.id == configured_voice:
                    pos = idx
            self.voice.SetSelection(pos)
        elif strategy is ReconciliationStrategies.save:
            self.config["engine"] = self.current_engine.name
            self.config["voice"] = self.voices[self.voice.GetSelection()].id
        super().reconcile(strategy=strategy)


class TTSGUIManager(ServiceGUIManager):

    def add_main_menu(self, menu):
        speechMenu = wx.Menu()
        # Speech menu
        speechMenu.Append(
            BookRelatedMenuIds.play,
            # Translators: the label of an ietm in the application menubar
            _("&Play\tF5"),
            # Translators: the help text of an ietm in the application menubar
            _("Start reading aloud"),
        )
        speechMenu.Append(
            BookRelatedMenuIds.pauseToggle,
            # Translators: the label of an ietm in the application menubar
            _("Pa&use/Resume\tF6"),
            # Translators: the help text of an ietm in the application menubar
            _("Pause/Resume reading aloud"),
        )
        speechMenu.Append(
            BookRelatedMenuIds.stop,
            # Translators: the label of an ietm in the application menubar
            _("&Stop\tF7"),
            # Translators: the help text of an ietm in the application menubar
            _("Stop reading aloud"),
        )
        speechMenu.Append(
            BookRelatedMenuIds.rewind,
            # Translators: the label of an ietm in the application menubar
            _("&Rewind\tAlt-LeftArrow"),
            # Translators: the help text of an ietm in the application menubar
            _("Skip to previous paragraph"),
        )
        speechMenu.Append(
            BookRelatedMenuIds.fastforward,
            # Translators: the label of an ietm in the application menubar
            _("&Fast Forward\tAlt-RightArrow"),
            # Translators: the help text of an ietm in the application menubar
            _("Skip to next paragraph"),
        )
        speechMenu.Append(
            ViewerMenuIds.voiceProfiles,
            # Translators: the label of an ietm in the application menubar
            _("&Voice Profiles\tCtrl-Shift-V"),
            # Translators: the help text of an ietm in the application menubar
            _("Manage voice profiles."),
        )
        speechMenu.Append(
            ViewerMenuIds.deactivateVoiceProfiles,
            # Translators: the label of an ietm in the application menubar
            _("&Deactivate Active Voice Profile"),
            # Translators: the help text of an ietm in the application menubar
            _("Deactivate the active voice profile."),
        )
        # Speech menu event handlers
        self.Bind(wx.EVT_MENU, self.onPlay, id=BookRelatedMenuIds.play)
        self.Bind(wx.EVT_MENU, self.onPauseToggle, id=BookRelatedMenuIds.pauseToggle)
        self.Bind(
            wx.EVT_MENU, lambda e: self.reader.rewind(), id=BookRelatedMenuIds.rewind
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.reader.fastforward(),
            id=BookRelatedMenuIds.fastforward,
        )
        self.Bind(wx.EVT_MENU, self.onStop, id=BookRelatedMenuIds.stop)
        self.Bind(wx.EVT_MENU, self.onVoiceProfiles, id=ViewerMenuIds.voiceProfiles)
        self.Bind(
            wx.EVT_MENU,
            self.onDeactivateVoiceProfile,
            id=ViewerMenuIds.deactivateVoiceProfiles,
        )

    def get_settings_panel(self):
        """Return a tuple of (insertion_order, panel)."""

    def add_toolbar_items(self, toolbar):
        self.ppr_id = wx.NewIdRef()
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(
            BookRelatedMenuIds.rewind,
            # Translators: the label of a button in the application toolbar
            _("Rewind"),
            images.rewind.GetBitmap(),
            # Translators: the help text of a button in the application toolbar
            _("Skip to previous paragraph"),
        )
        self.toolbar.AddTool(
            self.ppr_id,
            # Translators: the label of a button in the application toolbar
            _("Play"),
            images.play.GetBitmap(),
            # Translators: the help text of a button in the application toolbar
            _("Play/Resume"),
        )
        self.toolbar.AddTool(
            BookRelatedMenuIds.fastforward,
            # Translators: the label of a button in the application toolbar
            _("Fast Forward"),
            images.fastforward.GetBitmap(),
            # Translators: the help text of a button in the application toolbar
            _("Skip to next paragraph"),
        )
        self.toolbar.AddTool(
            ViewerMenuIds.voiceProfiles,
            # Translators: the label of a button in the application toolbar
            _("Voice"),
            images.profile.GetBitmap(),
            # Translators: the help text of a button in the application toolbar
            _("Customize TTS voice parameters."),
        )
        self.toolbar.AddSeparator()
    @gui_thread_safe
    def on_tts_state_changed(self, sender, state):
        if state is SynthState.busy:
            image = images.pause
        else:
            image = images.play
        self.toolbar.SetToolNormalBitmap(self.ppr_id, image.GetBitmap())
        if not self.reader.ready:
            return
        play = self.menuBar.FindItemById(BookRelatedMenuIds.play)
        pause_toggle = self.menuBar.FindItemById(BookRelatedMenuIds.pauseToggle)
        fastforward = self.menuBar.FindItemById(BookRelatedMenuIds.fastforward)
        rewind = self.menuBar.FindItemById(BookRelatedMenuIds.rewind)
        stop = self.menuBar.FindItemById(BookRelatedMenuIds.stop)
        pause_toggle.Enable(state is not SynthState.ready)
        stop.Enable(state is not SynthState.ready)
        play.Enable(state is not SynthState.busy)
        fastforward.Enable(state is not SynthState.ready)
        rewind.Enable(state is not SynthState.ready)

