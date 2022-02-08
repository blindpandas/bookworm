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
    RobustProgressDialog,
    SnakDialog,
    AsyncSnakDialog,
    ImmutableObjectListView,
    ColumnDefn,
)
from bookworm.utils import restart_application
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
            # Translators: label of a button
            updateTesseractBtn = wx.Button(tessBox, -1, _("Update Tesseract engine..."))
            self.Bind(wx.EVT_BUTTON, self.onDownloadTesseractLanguages, tessLangDlBtn)
            self.Bind(wx.EVT_BUTTON, self.onUpdateTesseractEngine, updateTesseractBtn)
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
        progress_dlg = RobustProgressDialog(
            self,
            # Translators: title of a progress dialog
            _("Downloading Tesseract OCR Engine"),
            # Translators: message of a progress dialog
            _("Getting download information..."),
            maxvalue=100,
            can_abort=True,
        )
        threaded_worker.submit(
            tesseract_download.download_tesseract_engine, progress_dlg
        ).add_done_callback(partial(self._after_tesseract_install, progress_dlg))

    def onDownloadTesseractLanguages(self, event):
        TesseractLanguageManager(
            title=_("Manage Tesseract OCR Engine Languages"), parent=self
        ).ShowModal()

    def _after_tesseract_install(self, progress_dlg, future):
        progress_dlg.Dismiss()
        if future.result() is True:
            wx.GetApp().mainFrame.notify_user(
                _("Restart Required"),
                _(
                    "Bookworm will now restart to complete the installation of the Tesseract OCR Engine."
                ),
            )
            wx.CallAfter(restart_application)

    def onUpdateTesseractEngine(self, event):
        AsyncSnakDialog(
            task=tesseract_download.is_new_tesseract_version_available,
            done_callback=self._on_update_tesseract_version_retreived,
            # Translators: message of a dialog
            message=_("Checking for updates. Please wait..."),
            parent=wx.GetApp().GetTopWindow(),
        )

    def _on_update_tesseract_version_retreived(self, future):
        try:
            if is_update_available := future.result():
                retval = wx.MessageBox(
                    _(
                        "A new version of Tesseract OCr engine is available for download.\nIt is strongly recommended to update to the latest version for the best accuracy and performance.\nWould you like to update to the new version?"
                    ),
                    _("Update Tesseract OCr Engine?"),
                    style=wx.YES_NO | wx.ICON_EXCLAMATION,
                )
                if retval != wx.YES:
                    return
                AsyncSnakDialog(
                    task=tesseract_download.remove_tesseract,
                    done_callback=lambda fut: self.onDownloadTesseractEngine(None),
                    # Translators: message of a dialog
                    message=_("Removing old Tesseract version. Please wait..."),
                    parent=wx.GetApp().GetTopWindow(),
                )
            else:
                wx.MessageBox(
                    # Translators: content of a message box
                    _("Your version of Tesseract OCR engine is up to date."),
                    # Translators: title of a message box
                    _("No updates"),
                    style=wx.ICON_INFORMATION,
                )
        except:
            log.exception(
                "Failed to check for updates for tesseract OCR engine", exc_info=True
            )
            wx.MessageBox(
                _("Failed to check for updates for Tesseract OCr engine."),
                _("Error"),
                style=wx.ICON_ERROR,
            )


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
    """
    A dialog to manage the languages for the managed
    version of Tesseract OCR Engine on Windows.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SetSize((600, -1))
        self.CenterOnScreen()

    def addControls(self, parent):
        self.notebookCtrl = wx.Notebook(parent, -1)
        panel_info = [
            (
                _("Installed Languages"),
                TesseractLanguagePanel(self.notebookCtrl, is_offline=True),
            ),
            (
                _("Downloadable Languages"),
                TesseractLanguagePanel(self.notebookCtrl, is_offline=False),
            ),
        ]
        for (label, panel) in panel_info:
            panel.SetSizerType("vertical")
            self.notebookCtrl.AddPage(panel, label)
        self.Bind(
            wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onNotebookPageChanged, self.notebookCtrl
        )
        self.notebookCtrl.GetCurrentPage().populate_list(set_focus=False)

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button to close a dialog
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        btnsizer.Realize()
        return btnsizer

    def onNotebookPageChanged(self, event):
        selected_page = self.notebookCtrl.GetPage(event.GetSelection())
        selected_page.populate_list(set_focus=False)


class TesseractLanguagePanel(sc.SizedPanel):
    def __init__(self, *args, is_offline, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_offline = is_offline
        self.online_languages = tesseract_download.get_downloadable_languages()

        # Translators: label of a list control containing bookmarks
        wx.StaticText(self, -1, _("Tesseract Languages"))
        listPanel = sc.SizedPanel(self)
        listPanel.SetSizerType("horizontal")
        listPanel.SetSizerProps(expand=True, align="center")
        self.tesseractLanguageList = ImmutableObjectListView(
            listPanel, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER, size=(500, -1)
        )
        self.btnPanel = btnPanel = sc.SizedPanel(self, -1)
        btnPanel.SetSizerType("horizontal")
        btnPanel.SetSizerProps(expand=True)
        if not self.is_offline:
            # Translators: text of a button to add a language to Tesseract OCR Engine (best quality model)
            self.addBestButton = wx.Button(
                btnPanel, wx.ID_ANY, _("Download &Best Model")
            )
            # Translators: text of a button to add a language to Tesseract OCR Engine (fastest model)
            self.addFastButton = wx.Button(
                btnPanel, wx.ID_ANY, _("Download &Fast Model")
            )
            self.Bind(wx.EVT_BUTTON, self.onAdd, self.addFastButton)
            self.Bind(wx.EVT_BUTTON, self.onAdd, self.addBestButton)
        else:
            # Translators: text of a button to remove a language from Tesseract OCR Engine
            self.removeButton = wx.Button(btnPanel, wx.ID_REMOVE, _("&Remove"))
            self.Bind(wx.EVT_BUTTON, self.onRemove, id=wx.ID_REMOVE)
        self.tesseractLanguageList.Bind(
            wx.EVT_SET_FOCUS, self.onListFocus, self.tesseractLanguageList
        )

    def populate_list(self, set_focus=True):
        installed_languages = [
            (True, info)
            for info in sorted(
                TesseractOcrEngine.get_recognition_languages(),
                key=lambda l: l.english_name,
            )
        ]
        if self.is_offline:
            languages = installed_languages
        else:
            languages = []
            added_locale_infos = set(l[1] for l in installed_languages)
            for lang in self.online_languages:
                loc_info = LocaleInfo.from_three_letter_code(lang)
                if loc_info in added_locale_infos:
                    continue
                else:
                    languages.append((False, loc_info))
                    added_locale_infos.add(loc_info)
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
        if set_focus:
            self.tesseractLanguageList.set_objects(languages, focus_item=0)
        else:
            self.tesseractLanguageList.set_objects(languages, set_focus=False)
        # Maintain the state of the list
        if not any(languages):
            if not self.is_offline:
                self.addBestButton.Enable(False)
                self.addFastButton.Enable(False)
            else:
                self.removeButton.Enable(False)
            self.btnPanel.Enable(False)

    def onAdd(self, event):
        if (selected := self.tesseractLanguageList.get_selected()) is None:
            return
        lang = selected[1]
        variant = "best" if event.GetEventObject() == self.addBestButton else "fast"
        lang_code = lang.given_locale_name
        if lang_code not in self.online_languages:
            log.debug(f"Could not find download info for language {lang_code}")
            return
        target_file = tesseract_download.get_language_path(lang_code)
        if target_file.exists():
            msg = wx.MessageBox(
                # Translators: content of a messagebox
                _(
                    "A version of the selected language model already exists.\n"
                    "Are you sure you want to replace it."
                ),
                # Translators: title of a message box
                _("Confirm"),
                style=wx.YES_NO | wx.ICON_WARNING,
                parent=self,
            )
            if msg == wx.NO:
                return
        try:
            target_file.unlink(missing_ok=True)
        except:
            return
        progress_dlg = RobustProgressDialog(
            wx.GetApp().mainFrame,
            # Translators: title of a progress dialog
            _("Downloading Language"),
            # Translators: content of a progress dialog
            _("Getting download information..."),
            maxvalue=100,
            can_hide=True,
            can_abort=True,
        )
        threaded_worker.submit(
            tesseract_download.download_language,
            lang_code,
            variant,
            target_file,
            progress_dlg,
        ).add_done_callback(
            lambda future: wx.CallAfter(
                self._after_download_language, progress_dlg, future
            )
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

    def onListFocus(self, event):
        if self.tesseractLanguageList.get_selected() is None:
            self.tesseractLanguageList.set_focused_item(0)

    def _after_download_language(self, progress_dlg, future):
        progress_dlg.Dismiss()
        try:
            if future.result():
                wx.GetApp().mainFrame.notify_user(
                    # Translators: title of a messagebox
                    _("Language Added"),
                    _("The Language Model was downloaded successfully."),
                    parent=self,
                )
                self.populate_list()
        except ConnectionError:
            log.exception("Failed to download language data from {url}", exc_info=True)
            wx.GetApp().mainFrame.notify_user(
                # Translators: title of a message box
                _("Connection Error"),
                # Translators: content of a messagebox
                _(
                    "Failed to download language data.\nPlease check your internet connection."
                ),
                icon=wx.ICON_ERROR,
            )
        except:
            log.exception("Failed to install language data from {url}", exc_info=True)
            wx.GetApp().mainFrame.notify_user(
                # Translators: title of a messagebox
                _("Error"),
                # Translators: content of a messagebox
                _("Failed to install language data.\nPlease try again later."),
                icon=wx.ICON_ERROR,
                parent=self,
            )
