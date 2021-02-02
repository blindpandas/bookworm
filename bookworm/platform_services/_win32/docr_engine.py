# coding: utf-8

import os
import clr
import platform
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.ocr_engines import OcrRequest, OcrResult, BaseOcrEngine
from bookworm.utils import NEWLINE
from bookworm.logger import logger
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
        recognized_text = docr_eng.recognize(
            ocr_request.imagedata,
            ocr_request.width,
            ocr_request.height
        )
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
        total = len(doc)
        out = StringIO()

        def recognize_page(page):
            image, width, height = page.get_image(zoom_factor, should_enhance)
            ocr_req = OcrRequest(
                language=lang,
                imagedata=image,
                width=width,
                height=height,
                cookie=page.number
            )
            return cls.recognize(ocr_req)

        with ThreadPoolExecutor(3) as pool:
            for (idx, res) in enumerate(pool.map(recognize_page, doc)):
                out.write(f"Page {res.cookie}{NEWLINE}{res.recognized_text}{NEWLINE}\f{NEWLINE}")
                channel.push(idx)
        with open(output_file, "w", encoding="utf8") as file:
            file.write(out.getvalue())
        out.close()
        doc.close()
        channel.close()
