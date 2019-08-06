# coding: utf-8

import wx
import wx.lib.sized_controls as sc
from enum import IntEnum, auto
from bookworm import app
from bookworm import config
from bookworm.utils import restart_application
from bookworm.i18n import get_available_languages, set_active_language
from bookworm.speech.engine import SpeechEngine
from bookworm.signals import config_updated
from bookworm.resources import images
from bookworm.logger import logger
from bookworm.config.spec import (
    PARAGRAPH_PAUSE_MAX,
    END_OF_PAGE_PAUSE_MAX,
    END_OF_SECTION_PAUSE_MAX,
)
from .components import SimpleDialog, EnhancedSpinCtrl


log = logger.getChild(__name__)
DEFAULT_STEP_SIZE = 5


class ReconciliationStrategies(IntEnum):
    load = auto()
    save = auto()


class SettingsPanel(sc.SizedPanel):

    config_section = None

    def __init__(self, parent, config_object=None):
        super().__init__(parent, -1)
        config_object = config_object or config.conf.config
        self.config = config_object[self.config_section]
        self.addControls()

    def addControls(self):
        raise NotImplementedError

    def get_state(self):
        for key, value in self.config.items():
            ctrl = self.FindWindowByName(f"{self.config_section}.{key}")
            if not ctrl:
                continue
            yield ctrl, key, value

    def reconcile(self, strategy=ReconciliationStrategies.load):
        for ctrl, key, value in self.get_state():
            if strategy is ReconciliationStrategies.load:
                ctrl.SetValue(value)
            elif strategy is ReconciliationStrategies.save:
                self.config[key] = ctrl.GetValue()
        if strategy is ReconciliationStrategies.save:
            config.save()
            config_updated.send(self, section=self.config_section)


class GeneralPanel(SettingsPanel):
    config_section = "general"

    def addControls(self):
        # Translators: the title of a group of controls in the
        # general settings page related to the UI
        UIBox = sc.SizedStaticBox(self, -1, _("User Interface"))
        UIBox.SetSizerProps(expand=True)
        # Translators: the label of a combobox containing display languages.
        wx.StaticText(UIBox, -1, _("Display Language:"))
        self.languageChoice = wx.Choice(UIBox, -1, style=wx.CB_SORT)
        self.languageChoice.SetSizerProps(expand=True)
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Speak user interface messages"),
            name="general.announce_ui_messages",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Open recently opened books from the last position"),
            name="general.open_with_last_position",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Use file name instead of book title"),
            name="general.show_file_name_as_title",
        )
        # Translators: the title of a group of controls shown in the
        # general settings page related to miscellaneous settings
        miscBox = sc.SizedStaticBox(self, -1, _("Miscellaneous"))
        miscBox.SetSizerProps(expand=True)
        wx.CheckBox(
            # Translators: the label of a checkbox
            miscBox,
            -1,
            _("Play pagination sound"),
            name="general.play_pagination_sound",
        )
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Play a sound when the current page contains notes"),
            name="general.play_page_note_sound",
        )
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Highlight bookmarked positions"),
            name="general.highlight_bookmarked_positions",
        )
        langobjs = get_available_languages().values()
        languages = set((lang.language, lang.description) for lang in langobjs)
        for ident, label in languages:
            self.languageChoice.Append(label, ident)
        self.languageChoice.SetStringSelection(app.current_language.description)

    def reconcile(self, strategy=ReconciliationStrategies.load):
        if strategy is ReconciliationStrategies.save:
            configured_lang = self.config["language"]
            selection = self.languageChoice.GetSelection()
            if selection == wx.NOT_FOUND:
                return
            selected_lang = self.languageChoice.GetClientData(selection)
            if selected_lang != configured_lang:
                self.config["language"] = selected_lang
                config.save()
                set_active_language(selected_lang)
                msg = wx.MessageBox(
                    # Translators: the content of a message asking the user to restart
                    _(
                        "You have changed the display language of Bookworm.\n"
                        "For this setting to fully take effect, you need to restart the application.\n"
                        "Would you like to restart the application right now?"
                    ),
                    # Translators: the title of a message telling the user
                    # that the display language have been changed
                    _("Language Changed"),
                    style=wx.YES_NO | wx.ICON_WARNING,
                )
                if msg == wx.YES:
                    restart_application()
        super().reconcile(strategy=strategy)


class SpeechPanel(SettingsPanel):
    config_section = "speech"

    def addControls(self):
        self.voices = SpeechEngine().get_voices()

        # Translators: the label of a group of controls in the
        # speech settings page related to voice selection
        voiceBox = sc.SizedStaticBox(self, -1, _("Voice"))
        voiceBox.SetSizerType("form")
        voiceBox.SetSizerProps(expand=True)
        # Translators: the label of a combobox containing a list of tts voices
        wx.StaticText(voiceBox, -1, _("Select Voice:"))
        self.voice = wx.Choice(voiceBox, -1, choices=[v.desc for v in self.voices])
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
        pausesBox = sc.SizedStaticBox(self, -1, _("Pauses"))
        pausesBox.SetSizerType("form")
        pausesBox.SetSizerProps(expand=True)
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
        for ctrl in (sp, pp, eop, eos):
            ctrl.SetSizerProps(expand=True)

    def reconcile(self, strategy=ReconciliationStrategies.load):
        if strategy is ReconciliationStrategies.load:
            configured_voice = self.config["voice"]
            pos = 0
            for idx, vinfo in enumerate(self.voices):
                if vinfo.name == configured_voice:
                    pos = idx
            self.voice.SetSelection(pos)
        elif strategy is ReconciliationStrategies.save:
            self.config["voice"] = self.voices[self.voice.GetSelection()].name
        super().reconcile(strategy=strategy)


class ReadingPanel(SettingsPanel):
    config_section = "reading"

    def addControls(self):
        # Translators: the title of a group of radio buttons in the reading page
        # in the application settings related to how to read.
        self.readingMode = wx.RadioBox(
            self,
            -1,
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
        # Translators: the title of a group of radio buttons in the reading page
        # in the application settings related to where to start reading from.
        self.reading_pos = wx.RadioBox(
            self,
            -1,
            _("Start reading from:"),
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            # Translators: the label of a radio button
            choices=[_("Cursor position"), _("Beginning of page")],
        )
        # Translators: the label of a group of controls in the reading page
        # of the settings related to behavior during reading  aloud
        miscBox = sc.SizedStaticBox(self, -1, _("During Reading Aloud"))
        miscBox.SetSizerProps(expand=True)
        # Translators: the label of a checkbox
        wx.CheckBox(
            miscBox, -1, _("Speak page number"), name="reading.speak_page_number"
        )
        # Translators: the label of a checkbox
        wx.CheckBox(
            miscBox,
            -1,
            _("Highlight spoken text"),
            name="reading.highlight_spoken_text",
        )
        wx.CheckBox(
            # Translators: the label of a checkbox
            miscBox,
            -1,
            _("Select spoken text"),
            name="reading.select_spoken_text",
        )
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Play end of section sound"),
            name="reading.play_end_of_section_sound",
        )

    def reconcile(self, strategy=ReconciliationStrategies.load):
        if strategy is ReconciliationStrategies.load:
            self.readingMode.SetSelection(self.config["reading_mode"])
            self.reading_pos.SetSelection(self.config["start_reading_from_"])
        elif strategy is ReconciliationStrategies.save:
            self.config["reading_mode"] = self.readingMode.GetSelection()
            self.config["start_reading_from_"] = self.reading_pos.GetSelection()
        super().reconcile(strategy=strategy)


class PreferencesDialog(SimpleDialog):
    """Preferences dialog."""

    imagefiles = ("general", "speech", "reading")

    def addControls(self, parent):
        self.tabs = wx.Listbook(parent, -1)

        # Image list
        image_list = wx.ImageList(24, 24)
        for imgname in self.imagefiles:
            bmp = getattr(images, imgname).GetBitmap()
            image_list.Add(bmp)
        self.tabs.AssignImageList(image_list)

        # Create settings pages
        generalPage = GeneralPanel(self.tabs)
        speechPage = SpeechPanel(self.tabs)
        readingPage = ReadingPanel(self.tabs)

        # Add tabs
        # Translators: the label of a page in the settings dialog
        self.tabs.AddPage(generalPage, _("General"), select=True, imageId=0)
        # Translators: the label of a page in the settings dialog
        self.tabs.AddPage(speechPage, _("Speech"), imageId=1)
        # Translators: the label of a page in the settings dialog
        self.tabs.AddPage(readingPage, _("Reading"), imageId=2)

        # Finalize
        self.SetButtonSizer(self.createButtonsSizer())
        # Event handlers
        self.Bind(wx.EVT_BUTTON, self.onSubmit, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.onApply, id=wx.ID_APPLY)
        self.Bind(wx.EVT_BUTTON, lambda e: self.Destroy(), id=wx.ID_CANCEL)

        # Initialize values
        self.reconcile_all(ReconciliationStrategies.load)
        self.tabs.GetListView().SetFocus()

    def getButtons(self, parent):
        return

    def reconcile_all(self, strategy):
        for num in range(0, self.tabs.GetPageCount()):
            page = self.tabs.GetPage(num)
            page.reconcile(strategy)

    def onSubmit(self, event):
        page = self.tabs.GetCurrentPage()
        page.reconcile(strategy=ReconciliationStrategies.save)
        self.Close()
        self.Destroy()

    def onApply(self, event):
        page = self.tabs.GetCurrentPage()
        page.reconcile(strategy=ReconciliationStrategies.save)
        self.tabs.GetListView().SetFocus()

    def createButtonsSizer(self):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the lable of the OK button in a dialog
        okBtn = wx.Button(self, wx.ID_OK, _("OK"))
        okBtn.SetDefault()
        # Translators: the lable of the cancel button in a dialog
        cancelBtn = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        # Translators: the lable of the apply button in a dialog
        applyBtn = wx.Button(self, wx.ID_APPLY, _("Apply"))
        for btn in (okBtn, cancelBtn, applyBtn):
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        return btnsizer
