# coding: utf-8

import os
import threading
import copy
import wx
from lru import LRU
from enum import IntEnum
from bookworm import app
from bookworm import config
from bookworm import speech
from bookworm.signals import (
    reader_book_unloaded,
    reader_page_changed,
    ocr_started,
    ocr_ended,
    speech_engine_state_changed
)
from bookworm.concurrency import call_threaded, process_worker
from bookworm.resources import sounds
from bookworm.speechdriver.enumerations import SynthState
from bookworm.gui.components import SimpleDialog, SnakDialog  
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from . import ocr_provider as ocr


log = logger.getChild(__name__)


class OCRMenuIds(IntEnum):
    scanCurrentPage = 10001
    autoScanPages = 10002
    scanToTextFile = 10003
    changeOCROptions = 10004


OCR_KEYBOARD_SHORTCUTS = {
    OCRMenuIds.scanCurrentPage: "F4",
    OCRMenuIds.autoScanPages: "Ctrl-F4",
}


class OCROptionsDialog(SimpleDialog):
    """OCR options."""

    def __init__(self, *args, saved_values=None, choices=(), force_save=False, **kwargs):
        self.saved_values = saved_values
        self.choices = choices
        self.force_save = force_save
        self._return_value = None
        super().__init__(*args, **kwargs)

    def addControls(self, parent):
        # Translators: the label of a combobox
        label = wx.StaticText(parent, -1, _("Recognition Language:"))
        self.langChoice = wx.Choice(parent, -1, choices=self.choices)
        self.langChoice.SetSizerProps(expand=True)
        wx.StaticText(parent, -1, _("Page image resolution::"))
        self.zoomFactorSlider = wx.Slider(parent, -1, minValue=1, maxValue=20)
        self.enhanceImageCheckbox = wx.CheckBox(
            parent,
            -1,
            # Translators: the label of a checkbox
            _("Enhance page image before recognition"),
        )
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
            self.zoomFactorSlider.SetValue(4)
            self.enhanceImageCheckbox.SetValue(True)
        else:
            self.langChoice.SetSelection(self.saved_values["lang"])
            self.zoomFactorSlider.SetValue(self.saved_values["zoom_factor"])
            self.enhanceImageCheckbox.SetValue(self.saved_values["should_enhance"])
            if not self.force_save:
                self.saveOptionsCheckbox.SetValue(self.saved_values["save_options"])

    def onOK(self, event):
        self._return_value = (
            self.langChoice.GetSelection(),
            self.zoomFactorSlider.GetValue(),
            self.enhanceImageCheckbox.IsChecked(),
            self.force_save or self.saveOptionsCheckbox.IsChecked()
        )
        self.Close()

    def ShowModal(self):
        super().ShowModal()
        return self._return_value


class OCRMenu(wx.Menu):
    """OCR menu."""

    def __init__(self, service, menubar):
        super().__init__()
        self.service = service
        self.menubar = menubar
        self.view = service.view
        self._ocr_cancelled = threading.Event()
        self._saved_ocr_options = []
        self._scanned_pages = LRU(size=100)

        # Add menu items
        self.Append(
            OCRMenuIds.scanCurrentPage,
            # Translators: the label of an item in the application menubar
            _("S&can Current Page...\tF4"),
            # Translators: the help text of an item in the application menubar
            _("OCR current page")
        )
        self.auto_scan_item = self.Append(
            OCRMenuIds.autoScanPages,
            # Translators: the label of an item in the application menubar
            _("&Realtime OCR\tCtrl-F4"),
            # Translators: the help text of an item in the application menubar
            _("Auto run  OCR when turning pages."),
            kind=wx.ITEM_CHECK
        )
        self.Append(
            OCRMenuIds.changeOCROptions,
            # Translators: the label of an item in the application menubar
            _("&Change OCR Options..."),
            # Translators: the help text of an item in the application menubar
            _("Change OCR options"),
        )
        self.Append(
            OCRMenuIds.scanToTextFile,
            # Translators: the label of an item in the application menubar
            _("Scan To Text File..."),
            # Translators: the help text of an item in the application menubar
            _("Scan pages and save the text to a .txt file."),
        )
        # Add the menu to the menubar
        # Translators: the label of the OCR menu in the application menubar
        self.view.toolsMenu.Insert(5, wx.ID_ANY, _("OCR Tools"), self)
        
        # Event handlers
        self.view.Bind(
            wx.EVT_MENU,
            self.onScanCurrentPage,
            id=OCRMenuIds.scanCurrentPage,
        )
        self.view.Bind(
            wx.EVT_MENU,
            self.onAutoScanPages,
            id=OCRMenuIds.autoScanPages,
        )
        self.view.Bind(
            wx.EVT_MENU,
            self.onScanToTextFile,
            id=OCRMenuIds.scanToTextFile,
        )
        self.view.Bind(
            wx.EVT_MENU,
            self.onChangeOCROptions,
            id=OCRMenuIds.changeOCROptions,
        )
        reader_book_unloaded.connect(self._on_reader_unloaded, sender=self.view.reader)
        reader_page_changed.connect(self._on_reader_page_changed, sender=self.service.reader)
        speech_engine_state_changed.connect(self._on_speech_engine_state_change, sender=self.view)

    def _get_ocr_options(self, from_cache=True, **dlg_kw):
        pre_saved = copy.copy(self._saved_ocr_options)
        if not from_cache:
            self._saved_ocr_options.clear()
            self._scanned_pages.clear()
        if self._saved_ocr_options:
            rv = self._saved_ocr_options
        else:
            self._saved_ocr_options.clear()
            langs = ocr.get_recognition_languages()
            if not langs:
                wx.MessageBox(
                    # Translators: content of a message
                    _("No language for OCR is present.\bPlease use Windos Regional Settings to download some languages."),
                    _("No OCR Languages"),
                    style=wx.ICON_ERROR
                )
                return
            saved_values = {}
            if pre_saved:
                saved_values["lang"] = [l.given_lang for l in langs].index(pre_saved[0])
                saved_values["zoom_factor"] = pre_saved[1]
                saved_values["should_enhance"] = pre_saved[2]
                saved_values["save_options"] = True
            dlg = OCROptionsDialog(parent=self.view, title=_("OCR Options"), choices=[l.description for l in langs], saved_values=saved_values, **dlg_kw)
            ocr_opts = dlg.ShowModal()
            if ocr_opts is None:
                return
            res = list(ocr_opts)
            res[0] = langs[res[0]].given_lang
            *rv, should_save = res
            if should_save:
                self._saved_ocr_options = rv
        return rv

    def onScanCurrentPage(self, event):
        self._ocr_cancelled.clear()
        res = self._get_ocr_options()
        if res is None:
            return speech.announce(_("Cancelled"), True)
        lang, zoom_factor, should_enhance = res
        reader =self.service.reader
        if reader.current_page in self._scanned_pages:
            self.view.set_content(self._scanned_pages[reader.current_page])
            return
        image, width, height = reader.document.get_page_image(reader.current_page, zoom_factor, should_enhance)
        args = (
            image, lang,
            width, height,
        )
        ocr_started.send(sender=self.view)
        # Show a modal dialog
        self._ocr_wait_dlg = SnakDialog(parent=self.view, message=_("Scanning page. Please wait...."), dismiss_callback=self._on_ocr_cancelled)
        self._ocr_wait_dlg.Show()
        sounds.ocr_start.play()
        process_worker.submit(ocr.recognize, *args, page_number=reader.current_page).add_done_callback(self._process_ocr_result)

    def onAutoScanPages(self, event):
        event.Skip()
        if not self._saved_ocr_options:
            self._get_ocr_options(force_save=True)
        if self.auto_scan_item.IsChecked():
            speech.announce(_("Realtime OCR is enabled"))
        else:
            speech.announce(_("Realtime OCR is disabled"))
        if not self.view.contentTextCtrl.GetValue():
            self.onScanCurrentPage(event)

    def onScanToTextFile(self, event):
        res = self._get_ocr_options(from_cache=False)
        if res is None:
            return
        lang, zoom_factor, should_enhance = res
        # Get output file path
        filename = f"{self.view.reader.current_book.title}.txt"
        saveExportedFD = wx.FileDialog(
            self.view,
            # Translators: the title of a save file dialog asking the user for a filename to export notes to
            _("Save as"),
            defaultDir=wx.GetUserHome(),
            defaultFile=filename,
            # Translators: file type in a save as dialog
            wildcard=_("Plain Text (*.txt)|.txt"),
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        if saveExportedFD.ShowModal() != wx.ID_OK:
            return
        output_file = saveExportedFD.GetPath().strip()
        saveExportedFD.Destroy()
        if not output_file:
            return
        # Continue with OCR
        document = self.service.reader.document
        dlg = wx.ProgressDialog(
            # Translators: the title of a progress dialog
            _("Scanning Pages"),
            # Translators: the message of a progress dialog
            _("Preparing book"),
            parent=self.view,
            maximum=len(document),
            style=wx.PD_APP_MODAL | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE,
        )        
        dlg.Update(progress, _("Scanning page {}").format(i))
        dlg.Close()
        dlg.Destroy()

    def onChangeOCROptions(self, event):
        self._get_ocr_options(from_cache=False)

    @gui_thread_safe
    def _process_ocr_result(self, task):
        if self._ocr_cancelled.is_set():
            ocr_ended.send(sender=self.view, isfaulted=True)
            return
        try:
            page_number, content = task.result()
        except Exception as e:
            self._ocr_wait_dlg.Hide()
            log.exception(f"Error getting OCR recognition results: {e}")
            ocr_ended.send(sender=self.view, isfaulted=True)
            return
        ocr_ended.send(sender=self.view, isfaulted=False)
        text = os.linesep.join(content)
        self._scanned_pages[page_number] = text
        if page_number == self.view.reader.current_page:
            self.view.set_content(text)
            sounds.ocr_end.play()
            speech.announce(_("Scan finished."), urgent=True)
            self._ocr_wait_dlg.Hide()
            self.view.contentTextCtrl.SetFocusFromKbd()

    def _on_ocr_cancelled(self):
        self._ocr_cancelled.set()
        speech.announce(_("OCR cancelled"), True)
        return True

    def _on_reader_unloaded(self, sender):
        self._saved_ocr_options.clear()
        self.auto_scan_item.Check(False)

    def _on_reader_page_changed(self, sender, current, prev):
        if self.auto_scan_item.IsChecked():
            self.onScanCurrentPage(None)

    def _on_speech_engine_state_change(self, sender, service, state):
        ...