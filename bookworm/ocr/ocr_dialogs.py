# coding: utf-8

import wx
import wx.lib.sized_controls as sc
from dataclasses import dataclass
from wx.adv import CommandLinkButton
from bookworm import app
from bookworm import config
from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.concurrency import threaded_worker
from bookworm.gui.settings import SettingsPanel, ReconciliationStrategies
from bookworm.gui.components import make_sized_static_box, SimpleDialog, SnakDialog
from bookworm.logger import logger
from bookworm.platform_services._win32 import tesseract_download
from bookworm.ocr_engines.tesseract_ocr_engine import TesseractOcrEngine
from bookworm.ocr_engines.image_processing_pipelines import (
    ImageProcessingPipeline,
    DebugProcessingPipeline,
    DPIProcessingPipeline,
    ThresholdProcessingPipeline,
    BlurProcessingPipeline,
    TwoInOneScanProcessingPipeline,
    DeskewProcessingPipeline,
    InvertColourProcessingPipeline,
    ErosionProcessingPipeline,
    DilationProcessingPipeline,
    ConcatImagesProcessingPipeline,
    SharpenColourProcessingPipeline,
)


log = logger.getChild(__name__)


@dataclass
class OcrOptions:
    language: LocaleInfo
    zoom_factor: float
    _ipp_enabled: int
    image_processing_pipelines: t.Tuple[ImageProcessingPipeline]
    store_options: bool


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
            choices=_engines_display,
        )
        # Translators: the label of a group of controls in the OCR page
        # of the settings related to Tesseract OCR engine
        tessBox = self.make_static_box(_("Tesseract OCR Engine"))
        if not tesseract_download.is_tesseract_available():
            tessEngineDlBtn = CommandLinkButton(
                tessBox,
                -1,
                _("Download Tesseract OCR Engine"),
                _(
                    "Get a free, high-quality OCR engine that supports over 100 languages."
                ),
            )
            self.Bind(wx.EVT_BUTTON, self.onDownloadTesseractEngine, tessEngineDlBtn)
        else:
            tessLangDlBtn = CommandLinkButton(
                tessBox,
                -1,
                _("Manage Tesseract OCR Languages"),
                _("Add support for new languages, and /or remove installed languages."),
            )
            self.Bind(wx.EVT_BUTTON, self.onDownloadTesseractLanguages, tessLangDlBtn)
        # Translators: the label of a group of controls in the reading page
        # of the settings related to image enhancement
        miscBox = self.make_static_box(_("Image processing"))
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Enable default image enhancement filters"),
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
                self._service._init_ocr_engine()
        super().reconcile(strategy=strategy)
        if strategy is ReconciliationStrategies.save:
            self._service._init_ocr_engine()

    def onDownloadTesseractEngine(self, event):
        threaded_worker.submit(tesseract_download.download_tesseract_engine, self)

    def onDownloadTesseractLanguages(self, event):
        ...


class OCROptionsDialog(SimpleDialog):
    """OCR options."""

    def __init__(
        self, *args, stored_options=None, languages=(), force_save=False, **kwargs
    ):
        self.stored_options = stored_options
        self.languages = languages
        self.force_save = force_save
        self._return_value = None
        self.image_processing_pipelines = []
        self.stored_ipp = (
            ()
            if self.stored_options is None
            else self.stored_options.image_processing_pipelines
        )
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        # Translators: the label of a combobox
        label = wx.StaticText(parent, -1, _("Recognition Language:"))
        self.langChoice = wx.Choice(
            parent, -1, choices=[l.description for l in self.languages]
        )
        self.langChoice.SetSizerProps(expand=True)
        wx.StaticText(parent, -1, _("Supplied Image resolution::"))
        self.zoomFactorSlider = wx.Slider(parent, -1, minValue=0, maxValue=10)
        # Translators: the label of a checkbox
        self.should_enhance_images = wx.CheckBox(
            parent, -1, _("Enable image enhancements")
        )
        ippPanel = sc.SizedPanel(parent)
        # Translators: the label of a checkbox
        imgProcBox = make_sized_static_box(
            ippPanel, _("Available image pre-processing filters:")
        )
        for (ipp_cls, lbl, should_enable) in self.get_image_processing_pipelines_info():
            chbx = wx.CheckBox(imgProcBox, -1, lbl)
            if self.stored_options is not None:
                chbx.SetValue(ipp_cls in self.stored_ipp)
            else:
                chbx.SetValue(should_enable)
            self.image_processing_pipelines.append((chbx, ipp_cls))
        wx.StaticLine(parent)
        if not self.force_save:
            self.storeOptionsCheckbox = wx.CheckBox(
                parent,
                -1,
                # Translators: the label of a checkbox
                _("&Save these options until I close the current book"),
            )
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        if self.stored_options is None:
            self.langChoice.SetSelection(0)
            self.zoomFactorSlider.SetValue(2)
            self.should_enhance_images.SetValue(config.conf["ocr"]["enhance_images"])
        else:
            self.langChoice.SetSelection(
                self.languages.index(self.stored_options.language)
            )
            self.zoomFactorSlider.SetValue(self.stored_options.zoom_factor)
            self.should_enhance_images.SetValue(self.stored_options._ipp_enabled)
            if not self.force_save:
                self.storeOptionsCheckbox.SetValue(self.stored_options.store_options)
        enable_or_disable_image_pipelines = lambda: ippPanel.Enable(
            self.should_enhance_images.IsChecked()
        )
        self.Bind(
            wx.EVT_CHECKBOX,
            lambda e: enable_or_disable_image_pipelines(),
            self.should_enhance_images,
        )
        enable_or_disable_image_pipelines()

    def onOK(self, event):
        if not self.should_enhance_images.IsChecked():
            selected_image_pp = []
        else:
            selected_image_pp = [
                ipp_cls
                for c, ipp_cls in self.image_processing_pipelines
                if c.IsChecked()
            ]
        self._return_value = OcrOptions(
            language=self.languages[self.langChoice.GetSelection()],
            zoom_factor=self.zoomFactorSlider.GetValue() or 1,
            _ipp_enabled=self.should_enhance_images.IsChecked(),
            image_processing_pipelines=selected_image_pp,
            store_options=self.force_save or self.storeOptionsCheckbox.IsChecked(),
        )
        self.Close()

    def ShowModal(self):
        super().ShowModal()
        return self._return_value

    def get_image_processing_pipelines_info(self):
        ipp = [
            (DPIProcessingPipeline, _("Increase image resolution"), True),
            (ThresholdProcessingPipeline, _("Binarization"), True),
            (
                TwoInOneScanProcessingPipeline,
                _("Split two-in-one scans to individual pages"),
                False,
            ),
            (ConcatImagesProcessingPipeline, _("Combine images"), False),
            (BlurProcessingPipeline, _("Blurring"), False),
            (DeskewProcessingPipeline, _("Deskewing"), False),
            (ErosionProcessingPipeline, _("Erosion"), False),
            (DilationProcessingPipeline, _("Dilation"), False),
            (SharpenColourProcessingPipeline, _("Sharpen image"), False),
            (InvertColourProcessingPipeline, _("Invert colors"), False),
        ]
        if app.debug:
            ipp.append((DebugProcessingPipeline, _("Debug"), False))
        return ipp
