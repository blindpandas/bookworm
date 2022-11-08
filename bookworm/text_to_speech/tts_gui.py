# coding: utf-8

from enum import IntEnum

import wx
import wx.lib.sized_controls as sc

from bookworm import speech
from bookworm.gui.components import EnhancedSpinCtrl, SimpleDialog
from bookworm.gui.settings import ReconciliationStrategies, SettingsPanel
from bookworm.logger import logger
from bookworm.speechdriver import DummySpeechEngine
from bookworm.speechdriver.enumerations import SynthState

from .tts_config import (
    END_OF_PAGE_PAUSE_MAX,
    END_OF_SECTION_PAUSE_MAX,
    PARAGRAPH_PAUSE_MAX,
)

log = logger.getChild(__name__)


class StatelessSpeechMenuIds(IntEnum):
    voiceProfiles = 255
    deactivateActiveVoiceProfile = wx.ID_REVERT


class StatefulSpeechMenuIds(IntEnum):
    play = 251
    playToggle = 252
    stop = 253
    pauseToggle = 254
    rewind = wx.ID_BACKWARD
    fastforward = wx.ID_FORWARD


SPEECH_KEYBOARD_SHORTCUTS = {
    StatefulSpeechMenuIds.play: "F5",
    StatefulSpeechMenuIds.pauseToggle: "F6",
    StatefulSpeechMenuIds.stop: "F7",
    StatelessSpeechMenuIds.voiceProfiles: "Ctrl-Shift-V",
}


class ReadingPanel(SettingsPanel):
    config_section = "reading"

    def addControls(self):
        # Translators: the label of a group of controls in the reading page
        generalReadingBox = self.make_static_box(_("Reading Options"))
        self.readingMode = wx.RadioBox(
            generalReadingBox,
            -1,
            # Translators: the title of a group of radio buttons in the reading page
            # in the application settings related to how to read.
            _("When Pressing Play:"),
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            choices=[
                # Translators: the label of a radio button
                _("Read the entire book"),
                # Translators: the label of a radio button
                _("Read the current section"),
                # Translators: the label of a radio button
                _("Read the current page"),
            ],
        )
        self.reading_pos = wx.RadioBox(
            self,
            -1,
            # Translators: the title of a group of radio buttons in the reading page
            # in the application settings related to where to start reading from.
            _("Start reading from:"),
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            # Translators: the label of a radio button
            choices=[_("Cursor position"), _("Beginning of page")],
        )
        # Translators: the label of a group of controls in the reading page
        # of the settings related to behavior during reading  aloud
        miscBox = self.make_static_box(_("During Reading Aloud"))
        wx.CheckBox(
            # Translators: the label of a checkbox
            miscBox,
            -1,
            _("Speak page number"),
            name="reading.speak_page_number",
        )
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Announce the end of sections"),
            name="reading.notify_on_section_end",
        )
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Ask to switch to a voice that speaks the language of the current book"),
            name="reading.ask_to_switch_voice_to_current_book_language",
        )
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Highlight spoken text"),
            name="reading.highlight_spoken_text",
        )
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Select spoken text"),
            name="reading.select_spoken_text",
        )

    def reconcile(self, strategy=ReconciliationStrategies.load):
        if strategy is ReconciliationStrategies.load:
            self.readingMode.SetSelection(self.config["reading_mode"])
            self.reading_pos.SetSelection(self.config["start_reading_from"])
        elif strategy is ReconciliationStrategies.save:
            self.config["reading_mode"] = self.readingMode.GetSelection()
            self.config["start_reading_from"] = self.reading_pos.GetSelection()
        super().reconcile(strategy=strategy)


class SpeechPanel(SettingsPanel):
    config_section = "speech"

    def __init__(self, *args, profile_name=None, **kwargs):
        self.service = wx.GetApp().service_handler.get_service("text_to_speech")
        self.profile_name = profile_name
        super().__init__(*args, **kwargs)

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
        self.engineSettingsPanel = engineSettingsPanel = sc.SizedPanel(voiceBox)
        # Translators: the label of a combobox containing a list of tts voices
        wx.StaticText(engineSettingsPanel, -1, _("Select Voice:"))
        self.voice = wx.Choice(engineSettingsPanel, -1)
        # Translators: the label of the speech rate slider
        wx.StaticText(engineSettingsPanel, -1, _("Speech Rate:"))
        self.rateSlider = wx.Slider(
            engineSettingsPanel, -1, minValue=0, maxValue=100, name="speech.rate"
        )
        self.rateSlider.SetPageSize(5)
        # Translators: the label of the voice pitch slider
        wx.StaticText(engineSettingsPanel, -1, _("Pitch:"))
        self.pitchSlider = wx.Slider(
            engineSettingsPanel, -1, minValue=0, maxValue=100, name="speech.pitch"
        )
        self.pitchSlider.SetPageSize(5)
        # Translators: the label of the speech volume slider
        wx.StaticText(engineSettingsPanel, -1, _("Speech Volume:"))
        self.volumeSlider = wx.Slider(
            engineSettingsPanel, -1, minValue=0, maxValue=100, name="speech.volume"
        )
        self.volumeSlider.SetPageSize(5)
        # Translators: the label of a group of controls in the speech
        # settings page related to speech pauses
        pausesBox = self.make_static_box(_("Pauses"), parent=engineSettingsPanel)
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
        self.changeEngineBtn.Enable(len(self.service.speech_engines) > 1)

    def configure_with_engine(self, engine_name=""):
        if (self.current_engine is not None) and (
            engine_name == self.current_engine.name
        ):
            return
        engine_name = engine_name or self.config["engine"]
        self.current_engine = self.service.get_engine(engine_name)
        self.engineInfoText.SetValue(_(self.current_engine.display_name))
        self.voices = self.current_engine().get_voices()
        self.voice.Clear()
        self.voice.Append([v.display_name for v in self.voices])
        self.reconcile()
        if self.current_engine is DummySpeechEngine:
            self.engineSettingsPanel.Enable(False)
            return
        else:
            self.engineSettingsPanel.Enable(True)

    def OnChoosEngine(self, event):
        current_engine_index = 0
        for (index, e) in enumerate(self.service.speech_engines):
            if e.name == self.current_engine.name:
                current_engine_index = index
        dlg = SpeechEngineSelector(
            [_(e.display_name) for e in self.service.speech_engines],
            current_engine_index,
            parent=self.Parent,
            title=_("Speech Engine"),
        )
        with dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.configure_with_engine(
                    self.service.speech_engines[dlg.GetValue()].name
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
            if self.voice.GetSelection() != wx.NOT_FOUND:
                self.config["voice"] = self.voices[self.voice.GetSelection()].id
        super().reconcile(strategy=strategy)
        if strategy is ReconciliationStrategies.load:
            self._set_default_engine_config()
        else:
            self.process_config_save()

    def _set_default_engine_config(self):
        if self.config.get("rate") == -1:
            self.rateSlider.Value = self.current_engine.default_rate
        if self.config.get("volume") == -1:
            self.volumeSlider.Value = self.current_engine.default_volume
        if self.config.get("pitch") == -1:
            self.volumeSlider.Value = self.current_engine.default_pitch

    def process_config_save(self):
        active_profile = self.service.config_manager.active_profile
        should_init_engine = active_profile is None and not self.profile_name
        if active_profile is not None and self.profile_name == active_profile["name"]:
            should_init_engine = True
        if self.service.is_engine_ready and should_init_engine:
            self.service.initialize_engine()


class VoiceProfileEditorDialog(SimpleDialog):
    """Edit a voice profile."""

    def __init__(self, parent, profile_name, profile):
        self.profile = profile
        # Translators: the title of a dialog to edit a voice profile
        title = _("Voice Profile: {profile}").format(profile=profile_name)
        super().__init__(parent, title)

    def addControls(self, parent):
        cPanel = self.spPanel = SpeechPanel(
            parent, config_object=self.profile, profile_name=self.profile["name"]
        )
        self.Bind(wx.EVT_BUTTON, self.onSubmit, id=wx.ID_OK)
        cPanel.reconcile()
        cPanel.Children[0].Children[1].SetFocus()

    def onSubmit(self, event):
        self.spPanel.reconcile(ReconciliationStrategies.save)
        self.profile.write()
        self.Close()


class VoiceProfileDialog(SimpleDialog):
    """Voice Profiles."""

    def __init__(self, *args, **kwargs):
        self.service = wx.GetApp().service_handler.get_service("text_to_speech")
        self.config_manager = self.service.config_manager
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
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
        self.CenterOnParent()
        self.refresh_profile_list()

    def refresh_profile_list(self):
        self.voiceProfilesChoice.Clear()
        self.config_manager.refresh_voice_profiles()
        profiles = list(sorted(self.config_manager.profiles.keys()))
        self.voiceProfilesChoice.SetFocus()
        for btn in (wx.ID_EDIT, wx.ID_DEFAULT, wx.ID_REMOVE):
            self.FindWindowById(btn).Enable(bool(profiles))
        if not profiles:
            return
        sel = 0
        active_profile = self.config_manager.active_profile
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
        active_profile = self.config_manager.active_profile
        if active_profile and profile_name == active_profile["name"]:
            self.Close()
            return wx.Bell()
        self.activate_profile(profile_name)
        self.Close()

    def activate_profile(self, profile_name):
        if profile_name not in self.config_manager.profiles:
            return
        self.config_manager.active_profile = self.config_manager.profiles[profile_name]
        if self.service.reader.ready:
            self.service.initialize_engine()
        self.service.view.menuBar.FindItemById(
            StatelessSpeechMenuIds.deactivateActiveVoiceProfile
        ).Enable(True)

    def onEdit(self, event):
        profile_name = self.selected_profile
        profile = self.config_manager.profiles.get(profile_name)
        if not profile:
            return wx.Bell()
        with VoiceProfileEditorDialog(
            self, profile_name=profile_name, profile=profile
        ) as dlg:
            dlg.ShowModal()
        if (
            self.config_manager.active_profile
            and profile_name == self.config_manager.active_profile["name"]
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
            profile = self.config_manager.create_voice_profile(profile_name)
        except ValueError:
            wx.MessageBox(
                # Translators: the content of a message notifying the user
                # user of the existence of a voice profile with the same name
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
        if profile_name not in self.config_manager.profiles:
            return wx.Bell()
        elif (
            self.config_manager.active_profile
            and self.config_manager.active_profile["name"] == profile_name
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
            self.config_manager.delete_voice_profile(profile_name)
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


class SpeechMenu(wx.Menu):
    """Main menu."""

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.view = service.view
        self.menubar = self.view.menuBar

        # Add menu items
        self.Append(
            StatefulSpeechMenuIds.play,
            # Translators: the label of an item in the application menubar
            _("&Play\tF5"),
            # Translators: the help text of an item in the application menubar
            _("Start reading aloud"),
        )
        self.Append(
            StatefulSpeechMenuIds.pauseToggle,
            # Translators: the label of an item in the application menubar
            _("Pa&use/Resume\tF6"),
            # Translators: the help text of an item in the application menubar
            _("Pause/Resume reading aloud"),
        )
        self.Append(
            StatefulSpeechMenuIds.stop,
            # Translators: the label of an item in the application menubar
            _("&Stop\tF7"),
            # Translators: the help text of an item in the application menubar
            _("Stop reading aloud"),
        )
        self.Append(
            StatefulSpeechMenuIds.rewind,
            # Translators: the label of an item in the application menubar
            _("&Rewind\tAlt-LeftArrow"),
            # Translators: the help text of an item in the application menubar
            _("Skip to previous paragraph"),
        )
        self.Append(
            StatefulSpeechMenuIds.fastforward,
            # Translators: the label of an item in the application menubar
            _("&Fast Forward\tAlt-RightArrow"),
            # Translators: the help text of an item in the application menubar
            _("Skip to next paragraph"),
        )
        self.Append(
            StatelessSpeechMenuIds.voiceProfiles,
            # Translators: the label of an item in the application menubar
            _("&Voice Profiles\tCtrl-Shift-V"),
            # Translators: the help text of an item in the application menubar
            _("Manage voice profiles."),
        )
        self.Append(
            StatelessSpeechMenuIds.deactivateActiveVoiceProfile,
            # Translators: the label of an item in the application menubar
            _("&Deactivate Active Voice Profile"),
            # Translators: the help text of an item in the application menubar
            _("Deactivate the active voice profile."),
        )

        # Append the menu
        # EventHandlers
        self.view.Bind(wx.EVT_MENU, self.onPlay, id=StatefulSpeechMenuIds.play)
        self.view.Bind(
            wx.EVT_MENU, self.onPauseToggle, id=StatefulSpeechMenuIds.pauseToggle
        )
        self.view.Bind(
            wx.EVT_MENU,
            lambda e: self.service.rewind(),
            id=StatefulSpeechMenuIds.rewind,
        )
        self.view.Bind(
            wx.EVT_MENU,
            lambda e: self.service.fastforward(),
            id=StatefulSpeechMenuIds.fastforward,
        )
        self.view.Bind(wx.EVT_MENU, self.onStop, id=StatefulSpeechMenuIds.stop)
        self.view.Bind(
            wx.EVT_MENU, self.onVoiceProfiles, id=StatelessSpeechMenuIds.voiceProfiles
        )
        self.view.Bind(
            wx.EVT_MENU,
            self.onDeactivateVoiceProfile,
            id=StatelessSpeechMenuIds.deactivateActiveVoiceProfile,
        )
        self.view.Bind(
            wx.EVT_MENU, self.onPlayToggle, id=StatefulSpeechMenuIds.playToggle
        )
        self.view.contentTextCtrl.Bind(
            wx.EVT_KEY_UP, self.onKeyUp, self.view.contentTextCtrl
        )
        # Disable this when no voice profile is active
        self.FindItemById(StatelessSpeechMenuIds.deactivateActiveVoiceProfile).Enable(
            False
        )

    def onPlay(self, event):
        if not self.service.is_engine_ready:
            self.service.initialize_engine()
        elif self.service.engine.state is SynthState.busy:
            return wx.Bell()
        setattr(self.service, "_requested_play", True)
        if self.service.engine.state is SynthState.paused:
            return self.onPauseToggle(event)
        self.service.speak_page()

    def onPlayToggle(self, event):
        if (not self.service.is_engine_ready) or (
            self.service.engine.state is SynthState.ready
        ):
            self.onPlay(event)
        else:
            self.onPauseToggle(event)

    def onPauseToggle(self, event):
        if self.service.is_engine_ready:
            if self.service.engine.state is SynthState.busy:
                self.service.engine.pause()
                # Translators: a message that is announced when the speech is paused
                return speech.announce(_("Paused"))
            elif self.service.engine.state is SynthState.paused:
                self.service.engine.resume()
                # Translators: a message that is announced when the speech is resumed
                return speech.announce(_("Resumed"))
        wx.Bell()

    def onStop(self, event):
        if (
            self.service.is_engine_ready
            and self.service.engine.state is not SynthState.ready
        ):
            self.service.stop_speech(user_requested=True)
            # Translators: a message that is announced when the speech is stopped
            return speech.announce(_("Stopped"))
        wx.Bell()

    def onVoiceProfiles(self, event):
        # Translators: the title of the voice profiles dialog
        with VoiceProfileDialog(self.view, title=_("Voice Profiles")) as dlg:
            dlg.ShowModal()

    def onDeactivateVoiceProfile(self, event):
        config_manager = self.service.config_manager
        config_manager.active_profile = None
        self.service.configure_engine()
        self.menubar.FindItemById(
            StatelessSpeechMenuIds.deactivateActiveVoiceProfile
        ).Enable(False)
        self.service.stop_speech()
        self.service.initialize_engine()
        self.service.speak_page(start_pos=self.view.get_insertion_point())

    def onKeyUp(self, event):
        event.Skip(True)
        keycode = event.GetKeyCode()
        if event.GetModifiers() == wx.MOD_ALT:
            if keycode == wx.WXK_RIGHT:
                self.service.fastforward()
            elif keycode == wx.WXK_LEFT:
                self.service.rewind()
