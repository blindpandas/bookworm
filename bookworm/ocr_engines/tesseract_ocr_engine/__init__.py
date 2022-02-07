# coding: utf-8

import sys
import os
from pathlib import Path
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
    name = "tesseract_ocr"
    display_name = _("Tesseract OCR Engine")

    @classmethod
    def check(cls) -> bool:
        if sys.platform == "win32":
            tesseract_executable = get_tesseract_path().joinpath("tesseract.exe").resolve()
            if tesseract_executable.is_file():
                pytesseract.pytesseract.tesseract_cmd = os.fspath(tesseract_executable)
                return True
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
        recognized_text = pytesseract.image_to_string(
            ocr_request.image.to_pil(),
            ocr_request.language.given_locale_name,
            nice=1
        )
        return OcrResult(
            recognized_text=recognized_text,
            cookie=ocr_request.cookie,
        )
