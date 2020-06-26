# coding: utf-8

import os
import operator
import clr
from System.Globalization import CultureInfo
import platform
from concurrent.futures import ThreadPoolExecutor
from bookworm import typehints as t
from bookworm import app
from bookworm.runtime import UWP_SERVICES_AVAILABEL
from bookworm.i18n import LanguageInfo
from bookworm.logger import logger

log = logger.getChild(__name__)


_ocr_available = False
try:
    if UWP_SERVICES_AVAILABEL:
        from docrpy import DocrEngine
        _ocr_available = True
except Exception as e:
    log .error(f"Could not load the OCR functionality: {e}")


def is_ocr_available() -> bool:
    return platform.version().startswith("10") and _ocr_available


def get_recognition_languages() -> t.List[LanguageInfo]:
    langs = [LanguageInfo(lang) for lang in DocrEngine.get_supported_languages()]
    if langs:
        current_lang = 0
        possible = [
            CultureInfo.CurrentCulture.Parent.LCID,
            CultureInfo.CurrentCulture.LCID,
        ]
        for (i, lang) in enumerate(langs):
            if lang.LCID in possible:
                current_lang = i
                break
        langs.insert(0, langs.pop(current_lang))
    return langs


def recognize(lang_tag: str, imagedata: bytes, width: int, height: int, cookie: t.Any=None) -> t.Tuple[t.Any, str]:
    return cookie, DocrEngine(lang_tag).recognize(imagedata, width, height)


def scan_to_text(
    doc_cls: "BaseDocument",
    doc_path: t.PathLike,
    lang: str,
    zoom_factor: float,
    should_enhance: bool,
    output_file: t.PathLike,
    channel: "QPChannel"
):
    doc = doc_cls(doc_path)
    doc.read()
    total = len(doc)
    engine = DocrEngine(lang)
    scanned = []
    
    def recognize_page(page):
        return engine.recognize(*page.get_image(zoom_factor, should_enhance))

    with ThreadPoolExecutor(3) as pool:
        with open(output_file, "a", encoding="utf8") as file:
            for (idx, text) in enumerate(pool.map(recognize_page, doc)):
                file.write(f"Page{idx + 1}\r\n{text}\n\f\n")
                channel.push(idx)
    doc.close()
    channel.close()

