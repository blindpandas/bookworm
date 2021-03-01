# coding: utf-8

import sys
import time
import wx
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from tempfile import TemporaryFile
from zipfile import ZipFile
from pydantic import validator, BaseModel, HttpUrl
from bookworm import typehints as t
from bookworm import app
from bookworm.http_tools import RemoteJsonResource, HttpResource
from bookworm.gui.components import RobustProgressDialog
from bookworm.ocr_engines.tesseract_ocr_engine import (
    TesseractOcrEngine,
    get_tesseract_path,
)
from bookworm.logger import logger

log = logger.getChild(__name__)
TESSERACT_INFO_URL = "http://localhost:5000/info.json"
_TESSERACT_INFO_CACHE = None


class TesseractDownloadInfo(BaseModel):
    engine_x86: HttpUrl
    engine_x64: HttpUrl
    languages: t.List[str]
    best_traineddata_base_url: HttpUrl
    fast_traineddata_base_url: HttpUrl

    def get_language_download_url(self, language: str, variant: str) -> HttpUrl:
        if language not in self.languages:
            raise ValueError(f"Language {language} is not available for download.")
        url = (
            self.best_traineddata_base_url
            if variant == "best"
            else self.fast_traineddata_base_url
        )
        return urljoin(url, f"{language}.traineddata")


def is_tesseract_available():
    return sys.platform == "win32" and TesseractOcrEngine.check_on_windows()


def get_tessdata():
    return get_tesseract_path() / "tessdata"


def get_language_path(language):
    return Path(get_tessdata(), f"{language}.traineddata")


def get_tesseract_download_info():
    global _TESSERACT_INFO_CACHE
    try:
        return (
            _TESSERACT_INFO_CACHE := _TESSERACT_INFO_CACHE
            if _TESSERACT_INFO_CACHE is not None
            else RemoteJsonResource(
                url=TESSERACT_INFO_URL,
                model=TesseractDownloadInfo,
            ).get()
        )
    except ConnectionError:
        log.exception("Failed to get Tesseract download info.", exc_info=True)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a messagebox
            _("Connection Error"),
            # Translators: content of a messagebox
            _(
                "Could not get Tesseract download information.\n"
                "Please check your internet connection and try again."
            ),
            icon=wx.ICON_ERROR,
        )
    except ValueError:
        log.exception("Error parsing tesseract download info", exc_info=True)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a message box
            _("Error"),
            # Translators: content of a message box
            _("Failed to parse Tesseract download information. Please try again."),
            icon=wx.ICON_ERROR,
        )


def download_tesseract_engine(parent):
    tesseract_directory = get_tesseract_path()
    info = get_tesseract_download_info()
    if info is None:
        return
    engine_dl_url = info.engine_x86 if app.arch == "x86" else info.engine_x64
    progress_dlg = RobustProgressDialog(
        parent,
        # Translators: title of a progress dialog
        _("Downloading Tesseract OCR Engine"),
        # Translators: message of a progress dialog
        _("Getting download information..."),
        maxvalue=100,
        can_hide=True,
        can_abort=True,
    )
    callback = lambda prog: progress_dlg.Update(prog.percentage, prog.user_message)
    try:
        dl_request = HttpResource(engine_dl_url).download()
        progress_dlg.set_abort_callback(dl_request.cancel)
        if dl_request.is_cancelled():
            return
        with TemporaryFile() as dlfile:
            dl_request.download_to_file(dlfile, callback)
            with progress_dlg.PulseContinuously(_("Extracting file...")):
                with ZipFile(dlfile, "r") as zfile:
                    tesseract_directory.mkdir(parents=True, exist_ok=True)
                    zfile.extractall(path=tesseract_directory)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a messagebox
            _("Success"),
            # Translators: content of a messagebox
            _("Tesseract engine downloaded successfully"),
            parent=parent,
        )
    except ConnectionError:
        log.debug("Failed to download tesseract orcr engine.", exc_info=True)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a messagebox
            _("Connection Error"),
            _(
                "Could not download Tesseract OCR Engine.\nPlease check your internet and try again."
            ),
            icon=wx.ICON_ERROR,
        )
    except:
        log.exception(
            "An error occurred while installing the Tesseract OCr Engine", exc_info=True
        )
        wx.GetApp().mainFrame.notify_user(
            _("Error"),
            _("Could not install the Tesseract OCR engine.\nPlease try again."),
            icon=wx.ICON_WARNING,
        )
    finally:
        progress_dlg.Dismiss()


def download_language(language, url):
    target_file = get_language_path(language)
    if target_file.exists():
        msg = wx.MessageBox(
            # Translators: content of a messagebox
            _(
                "A version of the selected language model already exists.\n"
                "Are you sure you want to replace it."
            ),
            # Translators: title of a messagebox
            _("Confirm"),
            style=wx.YES_NO | wx.ICON_WARNING,
        )
        if msg == wx.NO:
            return
    target_file.unlink(missing_ok=True)
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
    callback = lambda prog: progress_dlg.Update(prog.percentage, prog.user_message)
    try:
        dl_request = HttpResource(url).download()
        progress_dlg.set_abort_callback(dl_request.cancel)
        dl_request.download_to_filesystem(target_file, callback)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a messagebox
            _("Language Added"),
            _("The Language Model was downloaded succesfully."),
        )
    except ConnectionError:
        log.exception("Faild to download language data from {url}", exc_info=True)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a messagebox
            _("Connection Error"),
            # Translators: content of a messagebox
            _("Failed to download language data from {url}").format(url=url),
            icon=wx.ICON_ERROR,
        )
    finally:
        progress_dlg.Dismiss()
