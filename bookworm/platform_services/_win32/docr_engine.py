# coding: utf-8

import os
import platform
from concurrent.futures import ThreadPoolExecutor
from io import StringIO

import clr

from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from bookworm.ocr_engines import BaseOcrEngine, OcrRequest, OcrResult
from bookworm.utils import NEWLINE

from .runtime import UWP_SERVICES_AVAILABEL

log = logger.getChild(__name__)


_ocr_available = False
try:
    if UWP_SERVICES_AVAILABEL:
        from docrpy import DocrEngine as Win10DocrEngine

        _ocr_available = True
except Exception as e:
    log.error(f"Could not load the OCR functionality: {e}")


class DocrEngine(BaseOcrEngine):
    name = "docr"
    display_name = _("Windows 10 OCR")

    @classmethod
    def check(cls) -> bool:
        return platform.version().startswith("10") and _ocr_available

    @classmethod
    def get_recognition_languages(cls) -> t.List[LocaleInfo]:
        return [LocaleInfo(lang) for lang in Win10DocrEngine.get_supported_languages()]

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        docr_eng = Win10DocrEngine(ocr_request.language.ietf_tag)
        image = ocr_request.image.as_rgba()
        recognized_text = docr_eng.recognize(image.data, image.width, image.height)
        return OcrResult(
            recognized_text=recognized_text,
            cookie=ocr_request.cookie,
        )
