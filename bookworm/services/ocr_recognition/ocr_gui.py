# coding: utf-8

from bookworm.services import BookwormService, ServiceGUIManager

class OCRGUI(ServiceGUIManager):

    def add_main_menu(self, menu):
        """Add items to the main menu."""

    def add_context_menu(self, menu):
        """Add items to the content text control context menu."""

    def get_settings_panel(self):
        """Return a tuple of (insertion_order, panel)."""

    def add_toolbar_items(self, toolbar):
        """Return items to add to the application toolbar."""
