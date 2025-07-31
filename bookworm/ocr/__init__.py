# coding: utf-8

import more_itertools
import wx
from lru import LRU

from bookworm import config
from bookworm.logger import logger
from bookworm.ocr_engines import GENERIC_OCR_ENGINES
from bookworm.ocr_provider import PLATFORM_SPECIFIC_OCR_ENGINES
from bookworm.resources import sounds
from bookworm.service import BookwormService

from .ocr_dialogs import OcrPanel
from .ocr_menu import (
    OCR_KEYBOARD_SHORTCUTS,
    OCRMenu,
    OCRMenuIds,
    ocr_ended,
    ocr_started,
)

log = logger.getChild(__name__)
OCR_ENGINES = GENERIC_OCR_ENGINES + PLATFORM_SPECIFIC_OCR_ENGINES
AVAILABLE_OCR_ENGINES = [ocr_eng for ocr_eng in OCR_ENGINES if ocr_eng.check()]
PAGE_CACHE_SIZE = 500
OCR_CONFIG_SPEC = {
    "ocr": dict(
        engine='string(default="")',
        enhance_images="boolean(default=True)",
        baidu_api_key='string(default="")',
        baidu_secret_key='string(default="")',
    )
}


class _OCRManagerMixin:
    _ocr_engines = OCR_ENGINES
    _available_ocr_engines = AVAILABLE_OCR_ENGINES

    @classmethod
    def get_ocr_engine_by_name(cls, engine_name):
        for ocr_engine in cls._available_ocr_engines:
            if ocr_engine.name == engine_name:
                return ocr_engine

    @classmethod
    def get_first_available_ocr_engine(cls):
        """Return the configured ocr engine or the first available one, None otherwise."""
        return cls.get_ocr_engine_by_name(
            config.conf["ocr"]["engine"]
        ) or more_itertools.first(cls._available_ocr_engines, None)

    def _init_ocr_engine(self):
        self.current_ocr_engine = self.get_first_available_ocr_engine()
        self.init_saved_options()

    def init_saved_options(self):
        self.stored_options = None
        self.saved_scanned_pages = LRU(size=PAGE_CACHE_SIZE)


class OCRSettingsService(_OCRManagerMixin, BookwormService):
    """A separate service to enable users to download Tesseract if they're not on Windows 10."""

    name = "ocr_settings"
    config_spec = OCR_CONFIG_SPEC
    has_gui = True

    @classmethod
    def check(cls):
        return True

    def get_settings_panels(self):
        return [
            # Translators: the label of a page in the settings dialog
            (30, "ocr", OcrPanel, _("OCR")),
        ]


class OCRService(_OCRManagerMixin, BookwormService):
    name = "ocr"
    stateful_menu_ids = OCRMenuIds
    has_gui = True

    @classmethod
    def check(cls):
        return any(cls._available_ocr_engines)

    def __post_init__(self):
        self.init_saved_options()

    def process_menubar(self, menubar):
        self.menu = OCRMenu(self)
        # Translators: the label of an item in the application menubar
        return (35, self.menu, _("OCR"))

    def get_toolbar_items(self):
        return [(42, "ocr", _("OCR"), None)]

    def get_keyboard_shortcuts(self):
        return OCR_KEYBOARD_SHORTCUTS

    def shutdown(self):
        if (dlg := getattr(self.menu, "_wait_dlg", None)) is not None:
            dlg.Dismiss()
