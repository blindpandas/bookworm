import platform
import threading

from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from bookworm.ocr_engines import BaseOcrEngine, OcrRequest, OcrResult
from bookworm.utils import NEWLINE

log = logger.getChild(__name__)


_ocr_available = False
try:
    from winrt.windows.globalization import Language
    from winrt.windows.graphics.imaging import (
        BitmapAlphaMode,
        BitmapPixelFormat,
        SoftwareBitmap,
    )
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import Buffer

    _ocr_available = True
except Exception:
    log.exception("Could not load the OCR functionality")


def _wait_for_async_operation(operation):
    completed = threading.Event()
    operation.completed = lambda _operation, _status: completed.set()
    completed.wait()
    return operation.get_results()


def _get_recognized_text(result):
    return "".join(f"{line.text}{NEWLINE}" for line in result.lines)


class DocrEngine(BaseOcrEngine):
    name = "docr"
    display_name = _("Windows 10 OCR")
    __supports_more_than_one_recognition_language__ = False

    @classmethod
    def check(cls) -> bool:
        return platform.version().startswith("10") and _ocr_available

    @classmethod
    def get_recognition_languages(cls) -> t.List[LocaleInfo]:
        return [
            LocaleInfo(language.language_tag, given_locale_name=language.language_tag)
            for language in OcrEngine.available_recognizer_languages
        ]

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        language_tag = ocr_request.language.given_locale_name
        ocr_engine = OcrEngine.try_create_from_language(Language(language_tag))
        if ocr_engine is None:
            message = f"OCR language is not supported: {language_tag}"
            raise ValueError(message)

        image = ocr_request.image.as_rgba()
        pixel_buffer = Buffer(len(image.data))
        pixel_buffer.length = len(image.data)
        memoryview(pixel_buffer)[:] = image.data

        with SoftwareBitmap.create_copy_with_alpha_from_buffer(
            pixel_buffer,
            BitmapPixelFormat.RGBA8,
            image.width,
            image.height,
            BitmapAlphaMode.STRAIGHT,
        ) as bitmap:
            operation = ocr_engine.recognize_async(bitmap)
            try:
                result = _wait_for_async_operation(operation)
            finally:
                operation.close()

        return OcrResult(
            recognized_text=_get_recognized_text(result),
            ocr_request=ocr_request,
        )
