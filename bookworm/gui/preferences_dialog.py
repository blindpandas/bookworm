# coding: utf-8

import wx
import wx.lib.sized_controls as sc
from enum import IntEnum, auto
from bookworm import app
from bookworm import config
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
        UIBox = sc.SizedStaticBox(self, -1, "User Interface")
        UIBox.SetSizerProps(expand=True)
        wx.CheckBox(
            UIBox,
            -1,
            "Speak user interface messages",
            name="general.announce_ui_messages",
        )
        wx.CheckBox(
            UIBox,
            -1,
            "Open recently opened books from the last position",
            name="general.open_with_last_position",
        )
        wx.CheckBox(
            UIBox,
            -1,
            "Use file name instead of book title",
            name="general.show_file_name_as_title",
        )
        miscBox = sc.SizedStaticBox(self, -1, "Miscellaneous")
        miscBox.SetSizerProps(expand=True)
        wx.CheckBox(
            miscBox, -1, "Play pagination sound", name="general.play_pagination_sound"
        )
        wx.CheckBox(
            miscBox,
            -1,
            "Play a sound when the current page contains notes",
            name="general.play_page_note_sound",
        )
        wx.CheckBox(
            miscBox,
            -1,
            "Highlight bookmarked positions",
            name="general.highlight_bookmarked_positions",
        )


class SpeechPanel(SettingsPanel):
    config_section = "speech"

    def addControls(self):
        self.voices = SpeechEngine().get_voices()

        voiceBox = sc.SizedStaticBox(self, -1, "Voice")
        voiceBox.SetSizerType("form")
        voiceBox.SetSizerProps(expand=True)
        wx.StaticText(voiceBox, -1, "Select Voice:")
        self.voice = wx.Choice(voiceBox, -1, choices=[v.desc for v in self.voices])
        wx.StaticText(voiceBox, -1, "Speech Rate:")
        rt = wx.Slider(voiceBox, -1, minValue=0, maxValue=100, name="speech.rate")
        rt.SetPageSize(DEFAULT_STEP_SIZE)
        wx.StaticText(voiceBox, -1, "Volume:")
        vol = wx.Slider(voiceBox, -1, minValue=0, maxValue=100, name="speech.volume")
        vol.SetPageSize(DEFAULT_STEP_SIZE)
        # self.granularity = wx.RadioBox(
            # None,
            # -1,
            # "Speech Granularity:",
            # style=wx.RA_SPECIFY_COLS,
            # choices=["Sentence", "Paragraph"],
        # )
        pausesBox = sc.SizedStaticBox(self, -1, "Pauses")
        pausesBox.SetSizerType("form")
        pausesBox.SetSizerProps(expand=True)
        wx.StaticText(pausesBox, -1, "Additional Pause At Sentence End (Ms)")
        sp = EnhancedSpinCtrl(
            pausesBox, -1, min=0, max=PARAGRAPH_PAUSE_MAX, name="speech.sentence_pause"
        )
        wx.StaticText(pausesBox, -1, "Additional Pause At Paragraph End (Ms)")
        pp = EnhancedSpinCtrl(
            pausesBox, -1, min=0, max=PARAGRAPH_PAUSE_MAX, name="speech.paragraph_pause"
        )
        wx.StaticText(pausesBox, -1, "End of Page Pause (ms)")
        eop = EnhancedSpinCtrl(
            pausesBox,
            -1,
            min=0,
            max=END_OF_PAGE_PAUSE_MAX,
            name="speech.end_of_page_pause",
        )
        wx.StaticText(pausesBox, -1, "End of Section Pause (ms)")
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
            # self.granularity.SetSelection(self.config["granularity"])
        elif strategy is ReconciliationStrategies.save:
            self.config["voice"] = self.voices[self.voice.GetSelection()].name
            # self.config["granularity"] = self.granularity.GetSelection()
        super().reconcile(strategy=strategy)


class ReadingPanel(SettingsPanel):
    config_section = "reading"

    def addControls(self):
        self.readingMode = wx.RadioBox(
            self,
            -1,
            "When Pressing Play:",
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            choices=[
                "Read the entire book",
                "Read the current section",
                "Read the current page",
            ],
        )
        self.reading_pos = wx.RadioBox(
            self,
            -1,
            "Start reading from:",
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            choices=["Cursor position", "Beginning of page"],
        )
        miscBox = sc.SizedStaticBox(self, -1, "During Reading Aloud")
        miscBox.SetSizerProps(expand=True)
        wx.CheckBox(miscBox, -1, "Speak page number", name="reading.speak_page_number")
        wx.CheckBox(
            miscBox, -1, "Highlight spoken text", name="reading.highlight_spoken_text"
        )
        wx.CheckBox(
            miscBox, -1, "Select spoken text", name="reading.select_spoken_text"
        )
        wx.CheckBox(
            miscBox,
            -1,
            "Play end of section sound",
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
        self.tabs.AddPage(generalPage, "General", select=True, imageId=0)
        self.tabs.AddPage(speechPage, "Speech", imageId=1)
        self.tabs.AddPage(readingPage, "Reading", imageId=2)

        # Finalize
        self.SetButtonSizer(
            self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL | wx.APPLY)
        )
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
