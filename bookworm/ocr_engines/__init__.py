# coding: utf-8

from .base import (
    BaseOcrEngine,
    OcrRequest,
    OcrResult,
    OcrError,
    OcrAuthenticationError,
    OcrNetworkError,
    OcrProcessingError,
)
from .tesseract_ocr_engine import TesseractOcrEngine
from .baidu_ocr import BaiduGeneralOcrEngine, BaiduAccurateOcrEngine
from .vivo_ocr import VivoOcrEngine
from .glm_ocr import GlmOcrEngine

GENERIC_OCR_ENGINES = [
    TesseractOcrEngine,
    BaiduGeneralOcrEngine,
    BaiduAccurateOcrEngine,
    VivoOcrEngine,
    GlmOcrEngine,
]
