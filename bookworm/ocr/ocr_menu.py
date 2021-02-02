# coding: utf-8

import os
import threading
import time
import wx
import functools
from pathlib import Path
from lru import LRU
from enum import IntEnum
from bookworm import app
from bookworm import config
from bookworm import speech
from bookworm.ocr_engines import OcrRequest
from bookworm.text_to_speech import speech_engine_state_changed
from bookworm.signals import (
    _signals,
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
)
from bookworm.concurrency import QueueProcess, call_threaded, threaded_worker
from bookworm.gui.settings import SettingsPanel, ReconciliationStrategies
from bookworm.resources import sounds
from bookworm.speechdriver.enumerations import SynthState
from bookworm.gui.components import SimpleDialog, SnakDialog
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from .ocr_dialogs import OCROptionsDialog


log = logger.getChild(__name__)
PAGE_CACHE_SIZE = 500

# Signals
ocr_started = _signals.signal("ocr-started")
ocr_ended = _signals.signal("ocr-ended")


class OCRMenuIds(IntEnum):
    scanCurrentPage = 10001
    autoScanPages = 10002
    scanToTextFile = 10003
    changeOCROptions = 10004


OCR_KEYBOARD_SHORTCUTS = {
    OCRMenuIds.scanCurrentPage: "F4",
    OCRMenuIds.autoScanPages: "Ctrl-F4",
}


class OCRMenu(wx.Menu):
    """OCR menu."""

    def __init__(self, service, menubar):
        super().__init__()
        self.service = service
        self.active_ocr_engine = self.service.get_first_available_ocr_engine()
        self.menubar = menubar
        self.view = service.view
        self._ocr_wait_dlg = SnakDialog(
            parent=self.view,
            message=_("Scanning page. Please wait...."),
            dismiss_callback=self._on_ocr_cancelled,
        )
        self._ocr_cancelled = threading.Event()
        self._saved_ocr_options = []
        self._scanned_pages = LRU(size=PAGE_CACHE_SIZE)
        image2textId = wx.NewIdRef()

        # Add menu items
        self.Append(
            OCRMenuIds.scanCurrentPage,
            # Translators: the label of an item in the application menubar
            _("S&can Current Page...\tF4"),
            # Translators: the help text of an item in the application menubar
            _("OCR current page"),
        )
        self.auto_scan_item = self.Append(
            OCRMenuIds.autoScanPages,
            # Translators: the label of an item in the application menubar
            _("&Automatic OCR\tCtrl-F4"),
            # Translators: the help text of an item in the application menubar
            _("Auto run  OCR when turning pages."),
            kind=wx.ITEM_CHECK,
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
        self.Append(
            image2textId,
            # Translators: the label of an item in the application menubar
            _("Image To Text..."),
            # Translators: the help text of an item in the application menubar
            _("Run OCR on an image."),
        )
        # Add the menu to the menubar
        # Translators: the label of the OCR menu in the application menubar
        self.view.toolsMenu.Append(wx.ID_ANY, _("OCR"), self)

        # Event handlers
        self.view.Bind(
            wx.EVT_MENU, self.onScanCurrentPage, id=OCRMenuIds.scanCurrentPage
        )
        self.view.Bind(wx.EVT_MENU, self.onAutoScanPages, id=OCRMenuIds.autoScanPages)
        self.view.Bind(wx.EVT_MENU, self.onScanToTextFile, id=OCRMenuIds.scanToTextFile)
        self.view.Bind(
            wx.EVT_MENU, self.onChangeOCROptions, id=OCRMenuIds.changeOCROptions
        )
        self.view.Bind(wx.EVT_MENU, self.onScanImageFile, id=image2textId)
        self.view.add_load_handler(self._on_reader_loaded)
        reader_book_unloaded.connect(self._on_reader_unloaded, sender=self.view.reader)
        reader_page_changed.connect(
            self._on_reader_page_changed, sender=self.service.reader
        )
        speech_engine_state_changed.connect(
            self._on_speech_engine_state_change, sender=self.view
        )

    def _get_ocr_options(self, from_cache=True, **dlg_kw):
        pre_saved = list(self._saved_ocr_options)
        if not from_cache:
            self._saved_ocr_options.clear()
            self._scanned_pages.clear()
        if self._saved_ocr_options:
            rv = self._saved_ocr_options
        else:
            saved_values = {}
            if pre_saved:
                saved_values["lang"] = pre_saved[0]
                saved_values["zoom_factor"] = pre_saved[1]
                saved_values["should_enhance"] = pre_saved[2]
                saved_values["save_options"] = True
            opts = self._get_ocr_options_from_dlg(saved_values=saved_values, **dlg_kw)
            if opts is None:
                return
            *rv, should_save = opts
            if should_save:
                self._saved_ocr_options = rv
        return rv

    def _get_ocr_options_from_dlg(self, saved_values=None, **dlg_kw):
        langs = self.active_ocr_engine.get_sorted_languages()
        if not langs:
            wx.MessageBox(
                # Translators: content of a message
                _(
                    "No language for OCR is present.\nPlease check Bookworm documentations to learn how to add new languages."
                ),
                # Translators: title for a message
                _("No OCR Languages"),
                style=wx.ICON_ERROR,
            )
            return
        dlg = OCROptionsDialog(
            parent=self.view,
            title=_("OCR Options"),
            languages=langs,
            saved_values=saved_values or {},
            **dlg_kw,
        )
        ocr_opts = dlg.ShowModal()
        if ocr_opts is not None:
            return list(ocr_opts)

    def onScanCurrentPage(self, event):
        self._ocr_cancelled.clear()
        res = self._get_ocr_options()
        if res is None:
            return speech.announce(_("Cancelled"), True)
        lang, zoom_factor, should_enhance = res
        reader = self.service.reader
        if reader.current_page in self._scanned_pages:
            self.view.set_content(self._scanned_pages[reader.current_page])
            return
        image, width, height = reader.document.get_page_image(
            reader.current_page, zoom_factor, should_enhance
        )

        def _ocr_callback(ocr_result):
            page_number = ocr_result.cookie
            content = ocr_result.recognized_text
            self._scanned_pages[page_number] = content
            if page_number == self.view.reader.current_page:
                self.view.set_content(content)
                self.view.set_text_direction(lang.is_rtl)

        self._run_ocr(
            lang, image, width, height, _ocr_callback, cookie=reader.current_page
        )

    def _run_ocr(self, lang, image, width, height, callback, cookie=None):
        ocr_request = OcrRequest(
            language=lang,
            imagedata=image,
            width=width,
            height=height,
            cookie=cookie
        )
        ocr_started.send(sender=self.view)
        # Show a modal dialog
        self._ocr_wait_dlg.Show()
        sounds.ocr_start.play()
        future_callback = functools.partial(self._process_ocr_result, callback)
        threaded_worker.submit(
            self.active_ocr_engine.recognize,
            ocr_request
        ).add_done_callback(future_callback)

    def onAutoScanPages(self, event):
        event.Skip()
        if not self._saved_ocr_options:
            self._get_ocr_options(force_save=True)
        if self.auto_scan_item.IsChecked():
            speech.announce(_("Automatic OCR is enabled"))
        else:
            speech.announce(_("Automatic OCR is disabled"))
        if not self.view.contentTextCtrl.GetValue():
            self.onScanCurrentPage(event)

    def onScanToTextFile(self, event):
        res = self._get_ocr_options(from_cache=False, force_save=True)
        if res is None:
            return
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
        progress_dlg = wx.ProgressDialog(
            # Translators: the title of a progress dialog
            _("Scanning Pages"),
            # Translators: the message of a progress dialog
            _("Preparing book"),
            parent=self.view,
            maximum=len(self.service.reader.document),
            style=wx.PD_APP_MODAL | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE,
        )
        self._continue_with_text_extraction(res, output_file, progress_dlg)

    @call_threaded
    def _continue_with_text_extraction(self, options, output_file, progress_dlg):
        lang, zoom_factor, should_enhance = options
        doc = self.service.reader.document
        total = len(doc)
        args = (doc, lang, zoom_factor, should_enhance, output_file)
        for progress in QueueProcess(target=self.active_ocr_engine.scan_to_text, args=args):
            wx.CallAfter(
                progress_dlg.Update,
                progress + 1,
                f"Scanning page {progress} of {total}",
            )
        wx.CallAfter(progress_dlg.Hide)
        wx.CallAfter(progress_dlg.Close)
        wx.CallAfter(progress_dlg.Destroy)
        wx.CallAfter(
            wx.MessageBox,
            _(
                "Successfully processed {} pages.\nExtracted text was written to: {}"
            ).format(total, output_file),
            _("OCR Completed"),
            wx.ICON_INFORMATION,
        )
        wx.CallAfter(self.view.contentTextCtrl.SetFocus)

    def onChangeOCROptions(self, event):
        self._get_ocr_options(from_cache=False)

    def onScanImageFile(self, event):
        from fitz import Pixmap

        wildcard = []
        all_exts = [
            ("*.png", _("Portable Network Graphics")),
            ("*.jpg", _("JPEG images")),
            ("*.bmp", _("Bitmap images")),
        ]
        for ext, name in all_exts:
            wildcard.append("{name} ({ext})|{ext}|".format(name=name, ext=ext))
        wildcard[-1] = wildcard[-1].rstrip("|")
        allfiles = ";".join(ext[0] for ext in all_exts)
        wildcard.insert(0, _("All supported image formats|{ext}|").format(ext=allfiles))
        openFileDlg = wx.FileDialog(
            self.view,
            # Translators: the title of a file dialog to browse to an image
            message=_("Choose image file"),
            defaultDir=str(Path.home()),
            wildcard="".join(wildcard),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if openFileDlg.ShowModal() == wx.ID_OK:
            filename = openFileDlg.GetPath().strip()
            openFileDlg.Destroy()
            if not filename or not os.path.isfile(filename):
                return
            image = Pixmap(filename)
            # Force include the alpha channel
            image = Pixmap(image, True)
            options = self._get_ocr_options_from_dlg(force_save=True)
            if not options:
                return
            lang, *__ = options

            def _ocr_callback(ocr_result):
                content = ocr_result.recognized_text
                if self.service.reader.ready:
                    self.view.unloadCurrentEbook()
                self.view.set_content(content)
                self.view.set_text_direction(lang.is_rtl)
                self.view.set_status(_("OCR Results"))

            self._run_ocr(
                lang, image.samples, image.w, image.h, _ocr_callback, cookie=None
            )

    @gui_thread_safe
    def _process_ocr_result(self, callback, task):
        if self._ocr_cancelled.is_set():
            ocr_ended.send(sender=self.view, isfaulted=True)
            return
        try:
            ocr_result = task.result()
        except Exception as e:
            self._ocr_wait_dlg.Hide()
            log.exception(f"Error getting OCR recognition results.", exc_info=True)
            ocr_ended.send(sender=self.view, isfaulted=True)
            return
        callback(ocr_result)
        sounds.ocr_end.play()
        speech.announce(_("Scan finished."), urgent=True)
        self._ocr_wait_dlg.Hide()
        self.view.contentTextCtrl.SetFocusFromKbd()
        ocr_ended.send(sender=self.view, isfaulted=False)

    def _on_ocr_cancelled(self):
        self._ocr_cancelled.set()
        speech.announce(_("OCR cancelled"), True)
        return True

    def _on_reader_loaded(self, sender):
        can_render = sender.document.can_render_pages
        for item_id in OCRMenuIds:
            self.Enable(item_id, can_render)

    def _on_reader_unloaded(self, sender):
        self._scanned_pages.clear()
        self._saved_ocr_options.clear()
        self.auto_scan_item.Check(False)

    def _on_reader_page_changed(self, sender, current, prev):
        if self.auto_scan_item.IsChecked():
            self.onScanCurrentPage(None)

    def _on_speech_engine_state_change(self, sender, service, state):
        ...
