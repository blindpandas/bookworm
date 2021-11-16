# coding: utf-8

from __future__ import annotations
import wx
from bookworm import typehints as t
from bookworm.logger import logger


log = logger.getChild(__name__)


class BookwormService:
    """Maintaining SRP using services."""

    name: str = None
    stateful_menu_ids: t.Iterable[int] = None
    has_gui: bool = False
    config_spec: t.Dict[str, str] = None

    def __init__(self, view: "BookViewer"):
        self.view = view
        self.reader = view.reader
        self.__post_init__()

    @classmethod
    def check(self) -> bool:
        """Return `True ` if this service is available."""
        return True

    def __post_init__(self):
        """Any initialization rutines go here."""

    def shutdown(self):
        """Called when the app is about to exit."""

    def process_menubar(self, menubar: wx.MenuBar):
        """Add items to the main menu."""

    def get_contextmenu_items(self) -> t.Iterable[t.Tuple[int, str, str, int]]:
        """Get items to add to  the content text control context menu."""
        return ()

    def get_settings_panels(
        self,
    ) -> t.Iterable[t.Tuple[int, str, "bookworm.gui.settings.SettingPanel", str]]:
        """Return a list of SettingsPanelBlueprint."""
        return ()

    def get_toolbar_items(self) -> t.Iterable[t.Tuple[int, str, str, int]]:
        """Return items to add to the application toolbar."""
        return ()

    def get_keyboard_shortcuts(self) -> t.Dict[int, str]:
        """Return a dictionary mapping control id's to keyboard shortcuts."""
        return {}
