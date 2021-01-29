# coding: utf-8

from . import PLATFORM

if PLATFORM == "win32":
    from ._win32.ocr_provider import (
        is_ocr_available,
        get_recognition_languages,
        recognize,
        scan_to_text,
    )
elif PLATFORM == "linux":
    from ._linux.ocr_provider import (
        is_ocr_available,
        get_recognition_languages,
        recognize,
        scan_to_text,
    )
