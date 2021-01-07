# coding: utf-8

__all__ = [
    "get_user_locale", "set_app_locale",
    "is_running_portable", "is_high_contrast_active",
    "shell_integrate", "shell_disintegrate",
    "is_ocr_available", "get_recognition_languages", "recognize", "scan_to_text",
    "TTS_ENGINES"
]

from .user import get_user_locale, set_app_locale
from .winruntime import is_running_portable, is_high_contrast_active
from .shell_integration import shell_integrate, shell_disintegrate
from .ocr_provider import is_ocr_available, get_recognition_languages, recognize, scan_to_text
from .speech_engines import OcSpeechEngine, SapiSpeechEngine

TTS_ENGINES = (OcSpeechEngine, SapiSpeechEngine,)
