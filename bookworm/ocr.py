# coding: utf-8

import clr
import platform
from pathlib import Path
from bookworm import app
from bookworm.i18n import LanguageInfo
from bookworm.paths import app_path
from bookworm.logger import logger

log = logger.getChild(__name__)


try:
    _ocr_dll = app_path("OCRProvider.dll")
    if not app.is_frozen:
        _ocr_dll = (
            Path.cwd()
            / "includes"
            / "sharp-onecore-synth"
            / "bin"
            / "Debug"
            / "OCRProvider.dll"
        )
    clr.AddReference(str(_ocr_dll))
    from OCRProvider import OCRProvider
    _ocr_available = True
except:
    raise
    _ocr_available = False


def is_ocr_available():
    return platform.version().startswith("10") and _ocr_available

def get_recognition_languages():
    return [LanguageInfo(lang) for lang in OCRProvider.GetRecognizableLanguages()]

def recognize(imagedata, lang, width, height, page_number, recognizer=None):
    ocr = recognizer or OCRProvider(lang)
    lines = ocr.Recognize(imagedata, width, height)
    return page_number, lines
