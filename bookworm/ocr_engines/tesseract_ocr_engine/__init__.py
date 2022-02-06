# coding: utf-8

import sys
import os
from pathlib import Path
from PIL import Image
from bookworm import typehints as t
from bookworm import app
from bookworm.i18n import LocaleInfo
from bookworm.paths import data_path
from bookworm.ocr_engines import OcrRequest, OcrResult, BaseOcrEngine
from bookworm.logger import logger
from . import pytesseract


log = logger.getChild(__name__)



def get_tesseract_path():
    return data_path(f"tesseract_ocr_{app.arch}").resolve()

class TesseractOcrEngine(BaseOcrEngine):
    name = "tesseract_ocr_alt"
    display_name = _("Tesseract OCR Engine (Alternative implementation)")

    @classmethod
    def check_on_windows(cls):
        return cls.check()
    @classmethod
    def check(cls) -> bool:
        if sys.platform == "win32":
            tesseract_executable = (get_tesseract_path() /  "tesseract.exe").resolve()
            pytesseract.pytesseract.tesseract_cmd = os.fspath(tesseract_executable)
        try:
            return any(pytesseract.get_languages())
        except:
            return False

    @classmethod
    def get_recognition_languages(cls) -> t.List[LocaleInfo]:
        langs = []
        for lng in pytesseract.get_languages():
            try:
                langs.append(LocaleInfo.from_three_letter_code(lng))
            except ValueError:
                continue
        return langs

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        img = Image.frombytes(
            "RGB",
            (ocr_request.image.width, ocr_request.image.height),
            ocr_request.image.data,
        )
        recognized_text = pytesseract.image_to_string(
            img, ocr_request.language.given_locale_name, nice=1
        )
        return OcrResult(
            recognized_text=recognized_text,
            cookie=ocr_request.cookie,
        )
