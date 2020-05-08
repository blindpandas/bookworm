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


class ImageRecognizer:
    __slots__ = ["imagedata", "lang", "width", "height", "cookie"]

    def __init__(self, lang, imagedata, width, height, cookie=0):
        self.lang = lang
        self.imagedata = imagedata
        self.width = width
        self.height = height
        self.cookie = cookie

    def recognize(self):
        lines = OCRProvider.Recognize(self.lang, self.imagedata, self.width, self.height)
        return self.cookie, os.linesep.join(lines)
