# coding: utf-8

from bookworm.logger import logger


log = logger.getChild(__name__)


class BookwormService:
    """Extend the core functionality."""

    name = None
    stateful_menu_ids = []
    has_gui = False
    config_spec = {}

    def __init__(self, view):
        self.view = view
        self.reader = view.reader
        self.__post_init__()

    @classmethod
    def check(self):
        """Return `True ` if this service is available."""
        return True

    def __post_init__(self):
        """Any initialization rutines go here."""

    def shutdown(self):
        """Called when the app is about to exit."""

    def process_menubar(self, menubar):
        """Add items to the main menu."""

    def get_contextmenu_items(self):
        """Get items to add to  the content text control context menu."""
        return ()

    def get_settings_panels(self):
        """Return a list of SettingsPanelBlueprint."""
        return ()

    def get_toolbar_items(self):
        """Return items to add to the application toolbar."""
        return ()

    def get_keyboard_shourtcuts(self):
        """Return a dictionary mapping control id's to keyboard shortcuts."""
        return {}
