# coding: utf-8

import shutil
import sys
from pathlib import Path
from tempfile import TemporaryFile
from urllib.parse import urljoin, urlsplit
from zipfile import ZipFile

import requests
import wx

from bookworm import app
from bookworm import typehints as t
from bookworm.http_tools import HttpResource, RemoteJsonResource
from bookworm.logger import logger
from bookworm.ocr_engines.tesseract_ocr_engine import (TesseractOcrEngine,
                                                       get_tesseract_path)

log = logger.getChild(__name__)


BRANCH = "develop"
TESSERACT_VERSION_URL = f"https://raw.githubusercontent.com/blindpandas/bookworm/{BRANCH}/packages/tesseract/version"
if app.arch == "x86":
    TESSERACT_ENGINE_DOWNLOAD_URL = f"https://raw.githubusercontent.com/blindpandas/bookworm/{BRANCH}/packages/tesseract/tesseract_x86.zip"
else:
    TESSERACT_ENGINE_DOWNLOAD_URL = f"https://raw.githubusercontent.com/blindpandas/bookworm/{BRANCH}/packages/tesseract/tesseract_x64.zip"
FAST_TRAINEDDATA_DOWNLOAD_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/{lang_code}.traineddata"
BEST_TRAINEDDATA_DOWNLOAD_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/{lang_code}.traineddata"


def get_downloadable_languages():
    return (
        "afr",
        "sqi",
        "amh",
        "ara",
        "hye",
        "asm",
        "aze_cyrl",
        "aze",
        "ben",
        "eus",
        "bel",
        "bos",
        "bre",
        "bul",
        "mya",
        "cat",
        "ceb",
        "chr",
        "chi_sim",
        "hrv",
        "ces",
        "dan",
        "nld",
        "dzo",
        "eng",
        "epo",
        "est",
        "fao",
        "fil",
        "fin",
        "fra",
        "glg",
        "kat_old",
        "kat",
        "deu",
        "ell",
        "guj",
        "heb",
        "hin",
        "hun",
        "isl",
        "ind",
        "gle",
        "ita_old",
        "ita",
        "jpn_vert",
        "jpn",
        "jav",
        "kan",
        "kaz",
        "khm",
        "kor_vert",
        "kor",
        "kmr",
        "kir",
        "lao",
        "lav",
        "lit",
        "ltz",
        "mkd",
        "msa",
        "mal",
        "mlt",
        "mri",
        "mar",
        "mon",
        "nep",
        "nor",
        "ori",
        "pus",
        "fas",
        "pol",
        "por",
        "pan",
        "que",
        "ron",
        "rus",
        "gla",
        "srp_latn",
        "srp",
        "snd",
        "sin",
        "slk",
        "slv",
        "spa_old",
        "spa",
        "sun",
        "swa",
        "swe",
        "tgk",
        "tam",
        "tat",
        "tel",
        "tha",
        "bod",
        "tir",
        "ton",
        "tur",
        "ukr",
        "urd",
        "uig",
        "uzb_cyrl",
        "uzb",
        "vie",
        "cym",
        "fry",
        "yid",
        "yor",
    )


def is_tesseract_available():
    return sys.platform == "win32" and TesseractOcrEngine.check()


def get_tessdata():
    return get_tesseract_path() / "tessdata"


def get_language_path(language):
    return Path(get_tessdata(), f"{language}.traineddata")


def is_new_tesseract_version_available():
    remote_version = requests.get(TESSERACT_VERSION_URL).text
    return TesseractOcrEngine.get_tesseract_version() != remote_version


def download_tesseract_engine(progress_dlg):
    tesseract_directory = get_tesseract_path()
    callback = lambda prog: progress_dlg.Update(prog.percentage, prog.user_message)
    try:
        dl_request = HttpResource(TESSERACT_ENGINE_DOWNLOAD_URL).download()
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


def download_language(lang_code, variant, target_file, progress_dlg):
    url_prefix = (
        BEST_TRAINEDDATA_DOWNLOAD_URL
        if variant == "best"
        else FAST_TRAINEDDATA_DOWNLOAD_URL
    )
    download_url = url_prefix.format(lang_code=lang_code)
    callback = lambda prog: progress_dlg.Update(prog.percentage, prog.user_message)
    dl_request = HttpResource(download_url).download()
    progress_dlg.set_abort_callback(dl_request.cancel)
    dl_request.download_to_filesystem(target_file, callback)
    return not dl_request.is_cancelled()


def remove_tesseract():
    tesseract_path = get_tesseract_path()
    shutil.rmtree(tesseract_path, ignore_errors=False)
