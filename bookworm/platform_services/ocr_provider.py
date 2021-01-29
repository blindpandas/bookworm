# coding: utf-8

import io
from PIL import Image
import pyocr
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from . import PLATFORM

log = logger.getChild(__name__)

if PLATFORM == "win32":
    from ._win32.ocr_provider import  scan_to_text
elif PLATFORM == "linux":
    from ._linux.ocr_provider import scan_to_text


_AVAILABLE_TOOLS = pyocr.get_available_tools()


def is_ocr_available():
    return pyocr.tesseract in _AVAILABLE_TOOLS


def get_recognition_languages():
    langs = []
    for lng in pyocr.tesseract.get_available_languages():
        try:
            langs.append(LocaleInfo.from_three_letter_code(lng))
        except ValueError:
            log.warning(f"Could not load language {lng}")
    return langs


def recognize(
    lang, imagedata, width, height, cookie=None
):
    image = Image.frombytes("RGBA", (width, height), imagedata)
    return cookie, pyocr.tesseract.image_to_string(image, "ara")