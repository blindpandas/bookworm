# coding: utf-8

import sys
import os
import pytesseract
from pathlib import Path
from PIL import Image
from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.paths import data_path
from bookworm.ocr_engines import OcrRequest, OcrResult, BaseOcrEngine
from bookworm.logger import logger


log = logger.getChild(__name__)


class TesseractOcrEngineAlt(BaseOcrEngine):
    name = "tesseract_ocr_alt"
    display_name = _("Tesseract OCR Engine (Alternative implementation)")

    @classmethod
    def check(cls) -> bool:
        if sys.platform == "win32":
            tesseract_path = data_path("tesseract_ocr", "tesseract.exe").resolve()
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
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

    @classmethod
    def scan_to_text(cls, *args, **kwargs):
        os.environ["OMP_THREAD_LIMIT"] = "2"
        # os.environ["TESSEDIT_DO_INVERT"] = "0"
        super().scan_to_text(*args, **kwargs)
