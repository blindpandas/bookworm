# coding: utf-8


from .base import OcrRequest, OcrResult, BaseOcrEngine
from .tesseract_ocr_engine import TesseractOcrEngine


GENERIC_OCR_ENGINES = [TesseractOcrEngine,]
