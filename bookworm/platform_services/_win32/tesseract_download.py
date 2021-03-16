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
TESSERACT_INFO_URL = "https://bookworm.capeds.net/tesseract_info.json"
_TESSERACT_INFO_CACHE = None


class TesseractDownloadInfo(BaseModel):
    engine_x86: HttpUrl
    engine_x64: HttpUrl
    languages: t.List[str]
    best_traineddata_base_url: HttpUrl
    fast_traineddata_base_url: HttpUrl

    def get_engine_download_url(self):
        return self.engine_x86 if app.arch == "x86" else self.engine_x64

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
    if _TESSERACT_INFO_CACHE is None:
        _TESSERACT_INFO_CACHE = RemoteJsonResource(
            url=TESSERACT_INFO_URL,
            model=TesseractDownloadInfo,
        ).get()
    return _TESSERACT_INFO_CACHE


def get_tesseract_download_info_from_future(future, parent):
    try:
        return future.result()
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
            parent=parent,
        )
    except:
        log.exception("Error getting tesseract download info", exc_info=True)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a message box
            _("Error"),
            # Translators: content of a message box
            _("Failed to parse Tesseract download information. Please try again."),
            icon=wx.ICON_ERROR,
            parent=parent,
        )


def download_tesseract_engine(engine_download_url, progress_dlg):
    tesseract_directory = get_tesseract_path()
    callback = lambda prog: progress_dlg.Update(prog.percentage, prog.user_message)
    try:
        dl_request = HttpResource(engine_download_url).download()
        progress_dlg.set_abort_callback(dl_request.cancel)
        with TemporaryFile() as dlfile:
            dl_request.download_to_file(dlfile, callback)
            if dl_request.is_cancelled():
                return
            with progress_dlg.PulseContinuously(_("Extracting file...")):
                with ZipFile(dlfile, "r") as zfile:
                    tesseract_directory.mkdir(parents=True, exist_ok=True)
                    zfile.extractall(path=tesseract_directory)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a messagebox
            _("Success"),
            # Translators: content of a messagebox
            _("Tesseract engine downloaded successfully"),
        )
        return True
    except ConnectionError:
        log.debug("Failed to download tesseract OCR engine.", exc_info=True)
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


def download_language(url, target_file, progress_dlg):
    callback = lambda prog: progress_dlg.Update(prog.percentage, prog.user_message)
    dl_request = HttpResource(url).download()
    progress_dlg.set_abort_callback(dl_request.cancel)
    dl_request.download_to_filesystem(target_file, callback)
    return not dl_request.is_cancelled()
