# coding: utf-8

import wx
from bookworm.gui.settings import SettingsPanel, ReconciliationStrategies
from bookworm.logger import logger


log = logger.getChild(__name__)


class ContReadingPanel(SettingsPanel):
    config_section = ""

    def addControls(self):
        # Translators: the label of a group of controls in the reading page
        generalReadingBox = self.make_static_box(_("Reading Options"))
        wx.CheckBox(
            generalReadingBox,
            -1,
            # Translators: the label of a checkbox to enable continuous reading
            _("Use continuous reading mode"),
            name="reading.use_continuous_reading",
        )
        self.readingMode = wx.RadioBox(
            self,
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
            miscBox, -1, _("Speak page number"), name="reading.speak_page_number"
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


