# coding: utf-8

import wx
from lru import LRU
from bookworm import config
from bookworm.resources import sounds
from bookworm.base_service import BookwormService
from bookworm.ocr_engines import GENERIC_OCR_ENGINES
from bookworm.platform_services.ocr_provider import PLATFORM_SPECIFIC_OCR_ENGINES
from bookworm.logger import logger
from .ocr_dialogs import OcrPanel
from .ocr_menu import (
    OCRMenuIds,
    OCRMenu,
    OCR_KEYBOARD_SHORTCUTS,
    ocr_started,
    ocr_ended,
)


log = logger.getChild(__name__)
PAGE_CACHE_SIZE = 500


OCR_CONFIG_SPEC = {
    "ocr": dict(
        engine='string(default="")',
        enhance_images="boolean(default=True)",
    )
}


class OCRService(BookwormService):
    name = "ocr"
    config_spec = OCR_CONFIG_SPEC
    stateful_menu_ids = OCRMenuIds
    has_gui = True
    _ocr_engines = GENERIC_OCR_ENGINES + PLATFORM_SPECIFIC_OCR_ENGINES
    _available_ocr_engines = [ocr_eng for ocr_eng in _ocr_engines if ocr_eng.check()]

    @classmethod
    def check(cls):
        return any(cls._available_ocr_engines)

    def __post_init__(self):
        self.init_saved_options()

    def process_menubar(self, menubar):
        self.menu = OCRMenu(self, menubar)

    def get_settings_panels(self):
        return [
            # Translators: the label of a page in the settings dialog
            (30, "ocr", OcrPanel, _("OCR")),
        ]

    def get_toolbar_items(self):
        return [(42, "ocr", _("OCR"), None)]

    def get_keyboard_shourtcuts(self):
        return OCR_KEYBOARD_SHORTCUTS

    def shutdown(self):
        if (dlg := getattr(self.menu, "_wait_dlg", None)) is not None:
            dlg.Dismiss()

    @classmethod
    def get_ocr_engine_by_name(cls, engine_name):
        for ocr_engine in cls._available_ocr_engines:
            if ocr_engine.name == engine_name:
                return ocr_engine

    def get_first_available_ocr_engine(self):
        """Return the configured ocr engine or the first available one, None otherwise."""
        return (
            self.get_ocr_engine_by_name(config.conf["ocr"]["engine"])
            or self._available_ocr_engines[0]
        )

    def _init_ocr_engine(self):
        self.current_ocr_engine = self.get_first_available_ocr_engine()
        self.init_saved_options()

    def init_saved_options(self):
        self.stored_options = None
        self.saved_scanned_pages = LRU(size=PAGE_CACHE_SIZE)
