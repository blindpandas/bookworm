# coding: utf-8

import os
import clr
from System.Globalization import CultureInfo
import platform
from pathlib import Path
from bookworm import app
from bookworm.runtime import UWP_SERVICES_AVAILABEL
from bookworm.i18n import LanguageInfo
from bookworm.paths import app_path
from bookworm.logger import logger

log = logger.getChild(__name__)


try:
    if UWP_SERVICES_AVAILABEL:
        from OCRProvider import OCRProvider
        _ocr_available = True
except:
    _ocr_available = False


def is_ocr_available():
    return platform.version().startswith("10") and _ocr_available

def get_recognition_languages():
    langs = [LanguageInfo(lang) for lang in OCRProvider.GetRecognizableLanguages()]
    if langs:
        current_lang = 0
        possible = [CultureInfo.CurrentCulture.Parent.LCID, CultureInfo.CurrentCulture.LCID]
        for (i, lang) in enumerate(langs):
            if lang.LCID in possible:
                current_lang = i
                break
        langs.insert(0, langs.pop(current_lang))
    return langs

def recognize(imagedata, lang, width, height, *, page_number=0, recognizer=None):
    ocr = recognizer or OCRProvider(lang)
    lines = ocr.Recognize(imagedata, width, height)
    return page_number, lines

