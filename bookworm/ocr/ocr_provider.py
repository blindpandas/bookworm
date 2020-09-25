# coding: utf-8

import os
import operator
import clr
from System.Globalization import CultureInfo
import platform
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from chemical import it, ChemicalException
from bookworm import typehints as t
from bookworm import app
from bookworm.runtime import UWP_SERVICES_AVAILABEL
from bookworm.i18n import LanguageInfo
from bookworm.utils import NEWLINE
from bookworm.logger import logger

log = logger.getChild(__name__)


_ocr_available = False
try:
    if UWP_SERVICES_AVAILABEL:
        from docrpy import DocrEngine

        _ocr_available = True
except Exception as e:
    log.error(f"Could not load the OCR functionality: {e}")


def is_ocr_available() -> bool:
    return platform.version().startswith("10") and _ocr_available


def get_recognition_languages() -> t.List[LanguageInfo]:
    langs = [LanguageInfo(lang) for lang in DocrEngine.get_supported_languages()]
    current_lang = None
    with suppress(ChemicalException):
        current_lang = it(langs).find(
            lambda lang: lang.should_be_considered_equal_to(app.current_language)
        )
    if current_lang is not None:
        langs.remove(current_lang)
        langs.insert(0, current_lang)
    return langs


def recognize(
    lang_tag: str, imagedata: bytes, width: int, height: int, cookie: t.Any = None
) -> t.Tuple[t.Any, str]:
    return cookie, DocrEngine(lang_tag).recognize(imagedata, width, height)


def scan_to_text(
    doc,
    lang: str,
    zoom_factor: float,
    should_enhance: bool,
    output_file: t.PathLike,
    channel: "QPChannel",
):
    total = len(doc)
    engine = DocrEngine(lang)
    out = StringIO()

    def recognize_page(page):
        return engine.recognize(*page.get_image(zoom_factor, should_enhance))

    with ThreadPoolExecutor(3) as pool:
        for (idx, text) in enumerate(pool.map(recognize_page, doc)):
            out.write(f"Page {idx + 1}{NEWLINE}{text}{NEWLINE}\f{NEWLINE}")
            channel.push(idx)
    with open(output_file, "w", encoding="utf8") as file:
        file.write(out.getvalue())
    out.close()
    doc.close()
    channel.close()
