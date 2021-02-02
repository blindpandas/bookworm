# coding: utf-8

from . import PLATFORM

if PLATFORM == "win32":
    from ._win32.docr_engine import DocrEngine
    PLATFORM_SPECIFIC_OCR_ENGINES = [DocrEngine,]
elif PLATFORM == "linux":
    PLATFORM_SPECIFIC_OCR_ENGINES = []
