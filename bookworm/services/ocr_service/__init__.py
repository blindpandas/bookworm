# coding: utf-8

from bookworm.services import BookwormService
from .ocr_gui import OCRGUI

class OCRService(BookwormService):
    name = "ocr"
    gui_manager = OCRGUI


    @classmethod
    def check(self):
        return True

    def __post_init__(self):
        """Any initialization rutines go here."""

    def setup_config(self, spec):
        """Set any configuration for this service."""

    def setup_event_handlers(self):
        """Set any event handlers for this service."""


