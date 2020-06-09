# coding: utf-8

import os
import operator
import clr
from System.Globalization import CultureInfo
import platform
from multiprocessing import RLock
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from bookworm import app
from bookworm.runtime import UWP_SERVICES_AVAILABEL
from bookworm.i18n import LanguageInfo
from bookworm.paths import app_path
from bookworm.concurrency import QueueProcess
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


class ImageRecognizer:
    __slots__ = ["imagedata", "lang", "width", "height", "cookie"]

    def __init__(self, lang, imagedata, width, height, cookie=0):
        self.lang = lang
        self.imagedata = imagedata
        self.width = width
        self.height = height
        self.cookie = cookie

    def recognize(self):
        lines = OCRProvider.Recognize(
            self.lang, self.imagedata, self.width, self.height
        )
        return self.cookie, os.linesep.join(lines)


def do_scan_to_text(
    doc_cls, doc_path, lang, zoom_factor, should_enhance, output_file, queue
):
    doc = doc_cls(doc_path)
    doc.read()
    total = len(doc)
    scanned = []
    pool = ProcessPoolExecutor(8)
    check_lock = RLock()
    recognizers = (get_recognizer(pn) for pn in range(total + 1))

    def get_recognizer(page_number):
        image, width, height = doc.get_page_image(
            page_number, zoom_factor, should_enhance
        )
        return ImageRecognizer(
            lang=lang, imagedata=image, width=width, height=height, cookie=page_number
        )

    def callback(future):
        result = future.result()
        queue.put(result[0])
        with check_lock:
            scanned.append(result)

    for recog in recognizers:
        pool.submit(recog.recognize).add_done_callback(callback)
    while True:
        with check_lock:
            if len(scanned) >= total:
                break
    scanned.sort()
    with open(output_file, "w") as file:
        content = "\f\r\n".join(s[1] for s in scanned)
        file.write(content)
    doc.close()
    queue.put(-1)


def scan_to_text(doc_cls, doc_path, lang, zoom_factor, should_enhance, output_file):
    args = (doc_cls, doc_path, lang, zoom_factor, should_enhance, output_file)
    process = QueueProcess(
        target=do_scan_to_text, args=args, name="bookworm-ocr-to-text"
    )
    process.start()
    while True:
        value = process.queue.get()
        if value == -1:
            break
        yield value
    process.join()
