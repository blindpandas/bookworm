# coding: utf-8

import sys
import os
import ctypes
from io import BytesIO, StringIO
from pathlib import Path
from PIL import Image
from more_itertools import chunked
from bookworm import typehints as t
from bookworm.utils import NEWLINE
from bookworm.i18n import LocaleInfo
from bookworm.paths import data_path
from bookworm.ocr_engines import OcrRequest, OcrResult, BaseOcrEngine
from bookworm.logger import logger


log = logger.getChild(__name__)


class TesseractOcrEngine(BaseOcrEngine):
    name = "tesseract_ocr"
    display_name = _("Tesseract OCR Engine")
    _libtesseract = None

    @staticmethod
    def _check_on_windows():
        tesseract_lib_path = data_path("tesseract_ocr").resolve()
        if tesseract_lib_path.exists():
            ctypes.windll.kernel32.AddDllDirectory(str(tesseract_lib_path))
            os.environ["TESSDATA_PREFIX"] = str(tesseract_lib_path / "tessdata")
            return True
        return False

    @classmethod
    def check(cls) -> bool:
        if sys.platform == "win32" and not cls._check_on_windows():
            return False
        from . import pyocr
        cls._libtesseract = pyocr.libtesseract
        return cls._libtesseract.is_available()

    @classmethod
    def get_recognition_languages(cls) -> t.List[LocaleInfo]:
        langs = []
        for lng in cls._libtesseract.get_available_languages():
            try:
                langs.append(LocaleInfo.from_three_letter_code(lng))
            except ValueError:
                continue
        return langs

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        img = Image.frombytes(
            "RGBA",
            (ocr_request.image.width, ocr_request.image.height),
            ocr_request.image.data
        )
        recognized_text = cls._libtesseract.image_to_string(img, ocr_request.language.given_locale_name)
        return OcrResult(
            recognized_text=recognized_text,
            cookie=ocr_request.cookie,
        )


    @classmethod
    def scan_to_text(
        cls,
        doc: "BaseDocument",
        lang: LocaleInfo,
        zoom_factor: float,
        should_enhance: bool,
        output_file: t.PathLike,
        channel: "QPChannel",
    ):
        #os.environ["OMP_THREAD_LIMIT"] = "2"
        cls.check()
        total = len(doc)
        out = StringIO()

        def page_to_pil(page):
            imagedata, width, height = page.get_image(zoom_factor, should_enhance)
            return Image.frombytes(
                "RGBA",
                (width, height),
                imagedata
            )

        for batch in chunked(range(0, total), 10):
            image_io = BytesIO()
            first, *rest = (page_to_pil(doc[i]) for i in batch)
            first.save(image_io, format="tiff", save_all=True, append_images=rest)
            image_io.seek(0)
            final_image = Image.open(image_io)
            final_image.save("Hello.tiff")
            recognized_text = cls._libtesseract.image_to_string(final_image, lang.given_locale_name)
            out.write(f"Page {NEWLINE}{recognized_text}{NEWLINE}\f{NEWLINE}")
            for num in batch:
                channel.push(num + 1)
        with open(output_file, "w", encoding="utf8") as file:
            file.write(out.getvalue())
        out.close()
        doc.close()
        channel.close()

