# coding: utf-8

import wx
from bookworm import config
from bookworm.resources import sounds
from bookworm.base_service import BookwormService
from bookworm.platform_services.ocr_provider import is_ocr_available
from bookworm.logger import logger
from .ocr_gui import OCRMenuIds, OCRMenu, OCR_KEYBOARD_SHORTCUTS, ocr_started, ocr_ended

log = logger.getChild(__name__)



class OCRService(BookwormService):
    name = "ocr"
    stateful_menu_ids = OCRMenuIds
    has_gui = True

    @classmethod
    def check(self):
        return is_ocr_available()

    def process_menubar(self, menubar):
        self.menu = OCRMenu(self, menubar)

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
