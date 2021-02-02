# coding: utf-8

import wx
from contextlib import suppress
from chemical import it, ChemicalException
from bookworm import config
from bookworm.resources import sounds
from bookworm.base_service import BookwormService
from bookworm.ocr_engines import GENERIC_OCR_ENGINES
from bookworm.platform_services.ocr_provider import PLATFORM_SPECIFIC_OCR_ENGINES
from bookworm.logger import logger
from .ocr_dialogs import     OcrPanel
from .ocr_menu import (
    OCRMenuIds,
    OCRMenu,
    OCR_KEYBOARD_SHORTCUTS,
    ocr_started,
    ocr_ended
)


log = logger.getChild(__name__)


OCR_CONFIG_SPEC = {
    "ocr": {
        "engine": 'string(default="")',
        "enhance_images": 'boolean(default=True)',
    }
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
        return True #return not cls._available_ocr_engines

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
        try:
            self.menu._ocr_wait_dlg.Destroy()
        except RuntimeError:
            # already destroyed
            pass

    @classmethod
    def get_ocr_engine_by_name(cls, engine_name):
        with suppress(ChemicalException):
            return it(cls._available_ocr_engines).find(lambda e: e.name == engine_name)

    def get_first_available_ocr_engine(self):
        """Return the configured ocr engine or the first available one, None otherwise.""" 
        if self.check():
                return (
                    self.get_ocr_engine_by_name(config.conf["ocr"]["engine"])
                    or self._available_ocr_engines[0]
                )
