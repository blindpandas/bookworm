# coding: utf-8

import sys
import os
import ctypes
from io import BytesIO, StringIO
from pathlib import Path
from PIL import Image
from more_itertools import chunked
from bookworm import typehints as t
from bookworm.utils import NEWLINE
from bookworm.i18n import LocaleInfo
from bookworm.paths import data_path
from bookworm.ocr_engines import OcrRequest, OcrResult, BaseOcrEngine
from bookworm.logger import logger


log = logger.getChild(__name__)


def get_tesseract_path():
    return data_path("tesseract_ocr").resolve()


class TesseractOcrEngine(BaseOcrEngine):
    name = "tesseract_ocr"
    display_name = _("Tesseract OCR Engine")
    _libtesseract = None

    @classmethod
    def check_on_windows(cls):
        tesseract_lib_path = get_tesseract_path()
        if tesseract_lib_path.exists():
            ctypes.windll.kernel32.AddDllDirectory(str(tesseract_lib_path))
            os.environ["TESSDATA_PREFIX"] = str(tesseract_lib_path / "tessdata")
            os.environ["PATH"] += os.pathsep + str(tesseract_lib_path)
            return True
        return False

    @classmethod
    def check(cls) -> bool:
        if sys.platform == "win32" and not cls.check_on_windows():
            return False
        from . import pyocr

        cls._libtesseract = pyocr.libtesseract
        return cls._libtesseract.is_available()

    @classmethod
    def get_recognition_languages(cls) -> t.List[LocaleInfo]:
        langs = []
        for lng in cls._libtesseract.get_available_languages():
            try:
                langs.append(LocaleInfo.from_three_letter_code(lng))
            except ValueError:
                continue
        return langs

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        img = Image.frombytes(
            "RGBA",
            (ocr_request.image.width, ocr_request.image.height),
            ocr_request.image.data,
        )
        recognized_text = cls._libtesseract.image_to_string(
            img, ocr_request.language.given_locale_name
        )
        return OcrResult(
            recognized_text=recognized_text,
            cookie=ocr_request.cookie,
        )
