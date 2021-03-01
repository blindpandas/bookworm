# coding: utf-8

import wx
import wx.lib.sized_controls as sc
from dataclasses import dataclass
from functools import partial
from wx.adv import CommandLinkButton
from bookworm import app
from bookworm import config
from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.concurrency import threaded_worker
from bookworm.gui.settings import SettingsPanel, ReconciliationStrategies
from bookworm.gui.components import (
    make_sized_static_box,
    SimpleDialog,
    SnakDialog,
    AsyncSnakDialog,
    ImmutableObjectListView,
    ColumnDefn,
)
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
        TesseractLanguageManager(
            title=_("Manage Tesseract OCR Engine Languages"), parent=self
        ).ShowModal()


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


class TesseractLanguageManager(SimpleDialog):
    """A dialog to manage the languages for the managed version of Tesseract OCR Engine on Windows."""

    def __init__(self, *args, **kwargs):
        self.online_languages = ()
        super().__init__(*args, **kwargs)
        self.SetSize((600, -1))
        self.CenterOnScreen()

    def addControls(self, parent):
        # Translators: label of a list control containing bookmarks
        wx.StaticText(parent, -1, _("Tesseract Languages"))
        self.tesseractLanguageList = ImmutableObjectListView(
            parent, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER
        )
        self.tesseractLanguageList.SetSizerProps(expand=True)
        self.btnPanel = btnPanel = sc.SizedPanel(parent, -1)
        btnPanel.SetSizerType("horizontal")
        btnPanel.SetSizerProps(expand=True)
        # Translators: text of a button to add a language to Tesseract OCR Engine (best quality model)
        self.addBestButton = wx.Button(btnPanel, wx.ID_ANY, _("Download &Best Model"))
        # Translators: text of a button to add a language to Tesseract OCR Engine (fastest model)
        self.addFastButton = wx.Button(btnPanel, wx.ID_ANY, _("Download &Fast Model"))
        # Translators: text of a button to remove a language from Tesseract OCR Engine
        self.removeButton = wx.Button(btnPanel, wx.ID_REMOVE, _("&Remove"))
        self.Bind(wx.EVT_BUTTON, self.onAdd, self.addFastButton)
        self.Bind(wx.EVT_BUTTON, self.onAdd, self.addBestButton)
        self.Bind(wx.EVT_BUTTON, self.onRemove, id=wx.ID_REMOVE)
        self.Bind(
            wx.EVT_LIST_ITEM_FOCUSED,
            self.onListFocusChanged,
            self.tesseractLanguageList,
        )
        AsyncSnakDialog(
            task=tesseract_download.get_tesseract_download_info,
            done_callback=self._on_tesseract_dl_info,
            message=_("Getting download information, please wait..."),
            parent=self,
        )

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button to close a dialog
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        btnsizer.Realize()
        return btnsizer

    def _on_tesseract_dl_info(self, future):
        if (info := future.result()) is not None:
            self.online_languages = info.languages
        self.populate_list()

    def populate_list(self):
        language_identifiers = set(
            (True, lang.given_locale_name)
            for lang in TesseractOcrEngine.get_recognition_languages()
        )
        _installed_langs = {lang[1].lower() for lang in language_identifiers}
        language_identifiers.update(
            (False, lang)
            for lang in self.online_languages
            if lang.lower() not in _installed_langs
        )
        languages = [
            (
                lang[0],
                LocaleInfo.from_three_letter_code(lang[1]),
            )
            for lang in sorted(language_identifiers, key=lambda l: l, reverse=True)
        ]
        column_defn = [
            ColumnDefn(
                # Translators: the title of a column in the Tesseract language list
                _("Language"),
                "left",
                450,
                lambda lang: lang[1].description,
            ),
            ColumnDefn(
                # Translators: the title of a column in the Tesseract language list
                _("Installed"),
                "center",
                100,
                lambda lang: _("Yes") if lang[0] else _("No"),
            ),
        ]
        self.tesseractLanguageList.set_columns(column_defn)
        self.tesseractLanguageList.set_objects(languages)
        # Maintain the state of the list
        should_enable = any(languages)
        self.addBestButton.Enable(should_enable)
        self.addFastButton.Enable(should_enable)
        self.removeButton.Enable(should_enable)
        self.btnPanel.Enable(should_enable)

    def onAdd(self, event):
        if (selected := self.tesseractLanguageList.get_selected()) is None:
            return
        lang = selected[1]
        variant = "best" if event.GetEventObject() == self.addBestButton else "fast"
        AsyncSnakDialog(
            task=tesseract_download.get_tesseract_download_info,
            done_callback=partial(
                self._on_download_language, lang.given_locale_name, variant
            ),
            message=_("Getting download information, please wait..."),
            parent=self,
        )

    def onRemove(self, event):
        if (selected := self.tesseractLanguageList.get_selected()) is None:
            return
        lang = selected[1]
        msg = wx.MessageBox(
            # Translators: content of a messagebox
            _("Are you sure you want to remove language:\n{lang}?").format(
                lang=lang.description
            ),
            # Translators: title of a messagebox
            _("Confirm"),
            style=wx.YES_NO | wx.ICON_WARNING,
        )
        if msg == wx.NO:
            return
        try:
            tesseract_download.get_language_path(lang.given_locale_name).unlink()
            self.populate_list()
        except:
            log.exception(f"Could not remove language {lang}", exc_info=True)

    def onListFocusChanged(self, event):
        if (selected := self.tesseractLanguageList.get_selected()) is not None:
            is_installed = selected[0]
            self.addBestButton.Enable(not is_installed)
            self.addFastButton.Enable(not is_installed)
            self.removeButton.Enable(is_installed)

    def _on_download_language(self, lang_name, variant, future):
        if (info := future.result()) is None:
            return
        if lang_name not in info.languages:
            log.debug(f"Could not find download info for language {lang_name}")
            return
        url = info.get_language_download_url(lang_name, variant=variant)
        threaded_worker.submit(
            tesseract_download.download_language, lang_name, url
        ).add_done_callback(lambda f: wx.CallAfter(self.populate_list))
