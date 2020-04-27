# coding: utf-8

from bookworm.logger import logger


log = logger.getChild(__name__)


class BookwormService:
    """Extend the core functionality."""
    name = None
    gui_manager = None

    def __init__(self, view, reader)):
        self.view = view
        self.reader = reader
        self.__post_init__()
        if self.gui_manager:
            self.gui = self.gui_manager(self)

    @classmethod
    def check(self):
        """Return `True ` if this service is available."""
        return True

    def __post_init__(self):
        """Any initialization rutines go here."""

    def setup_config(self, spec):
        """Set any configuration for this service."""

    def setup_event_handlers(self):
        """Set any event handlers for this service."""


class ServiceGUIManager:
    """Manages GUI of a service."""

    def __init__(self, service):
        self.service = service
        self.frame = self.service.view
        self.reader = self.service.reader

    def add_main_menu(self, menu):
        """Add items to the main menu."""

    def add_context_menu(self, menu):
        """Add items to the content text control context menu."""

    def get_settings_panel(self):
        """Return a tuple of (insertion_order, panel)."""

    def add_toolbar_items(self, toolbar):
        """Return items to add to the application toolbar."""
