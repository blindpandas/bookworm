# coding: utf-8


from .base import OcrRequest, OcrResult, BaseOcrEngine
from .tesseract_ocr_engine import TesseractOcrEngine
#from .tesseract_ocr_engine.tesseract_alt import TesseractOcrEngineAlt


GENERIC_OCR_ENGINES = [TesseractOcrEngine,]
