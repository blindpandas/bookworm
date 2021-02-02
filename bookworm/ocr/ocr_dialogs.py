# coding: utf-8

import wx
from bookworm import app
from bookworm import config
from bookworm.ocr_engines import OcrRequest
from bookworm.gui.settings import SettingsPanel, ReconciliationStrategies
from bookworm.gui.components import SimpleDialog, SnakDialog
from bookworm.logger import logger


log = logger.getChild(__name__)



class OcrPanel(SettingsPanel):
    config_section = "ocr"

    def addControls(self):
        self._service = wx.GetApp().service_handler.get_service("ocr")
        self._engines = self._service._available_ocr_engines
        _engines_display = [_(e.display_name) for e in self._engines]
        # Translators: the label of a group of controls in the reading page
        generalOcrBox = self.make_static_box(_("OCR Options"))
        self.ocrEngine = wx.RadioBox(
            generalOcrBox,
            -1,
            # Translators: the title of a group of radio buttons in the OCR page
            # in the application settings.
            _("Default OCR Engine"),
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            choices=_engines_display
        )
        # Translators: the label of a group of controls in the reading page
        # of the settings related to image enhancement
        miscBox = self.make_static_box(_("Image processing"))
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Enhance images before OCR"),
            name="ocr.enhance_images",
        )

    def reconcile(self, strategy=ReconciliationStrategies.load):
        if strategy is ReconciliationStrategies.load:
            self.ocrEngine.SetSelection(
                self._engines.index(self._service.get_first_available_ocr_engine())
            )
        elif strategy is ReconciliationStrategies.save:
            selected_engine = self._engines[self.ocrEngine.GetSelection()]
            if self.config["engine"] != selected_engine.name:
                self.config["engine"] = selected_engine.name
        super().reconcile(strategy=strategy)




class OCROptionsDialog(SimpleDialog):
    """OCR options."""

    def __init__(
        self, *args, saved_values=None, languages=(), force_save=False, **kwargs
    ):
        self.saved_values = saved_values
        self.languages = languages
        self.force_save = force_save
        self._return_value = None
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        # Translators: the label of a combobox
        label = wx.StaticText(parent, -1, _("Recognition Language:"))
        self.langChoice = wx.Choice(parent, -1, choices=[l.description for l in self.languages])
        self.langChoice.SetSizerProps(expand=True)
        wx.StaticText(parent, -1, _("Supplied Image resolution::"))
        self.zoomFactorSlider = wx.Slider(parent, -1, minValue=0, maxValue=10)
        # self.enhanceImageCheckbox = wx.CheckBox(
        # parent,
        # -1,
        # # Translators: the label of a checkbox
        # _("Enhance image before recognition"),
        # )
        wx.StaticLine(parent)
        if not self.force_save:
            self.saveOptionsCheckbox = wx.CheckBox(
                parent,
                -1,
                # Translators: the label of a checkbox
                _("&Save these options until I close the current book"),
            )
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        if not self.saved_values:
            self.langChoice.SetSelection(0)
            self.zoomFactorSlider.SetValue(1)
            # self.enhanceImageCheckbox.SetValue(True)
        else:
            self.langChoice.SetSelection(self.languages.index(self.saved_values["lang"]))
            self.zoomFactorSlider.SetValue(self.saved_values["zoom_factor"])
            # self.enhanceImageCheckbox.SetValue(self.saved_values["should_enhance"])
            if not self.force_save:
                self.saveOptionsCheckbox.SetValue(self.saved_values["save_options"])

    def onOK(self, event):
        self._return_value = (
            self.languages[self.langChoice.GetSelection()],
            self.zoomFactorSlider.GetValue() or 1,
            True,  # self.enhanceImageCheckbox.IsChecked(),
            self.force_save or self.saveOptionsCheckbox.IsChecked(),
        )
        self.Close()

    def ShowModal(self):
        super().ShowModal()
        return self._return_value

