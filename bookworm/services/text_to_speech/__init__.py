# coding: utf-8

from bookworm.services import BookwormService
from bookworm.logger import logger
from .tts_gui import ReadingPanel

log = logger.getChild(__name__)


# Some useful constants
PARAGRAPH_PAUSE_MAX = 5000
END_OF_PAGE_PAUSE_MAX = 7000
END_OF_SECTION_PAUSE_MAX = 9000


class TextToSpeechService(BookwormService):
    name = "text_to_speech"
    has_gui = True
    config_spec = {
        "reading": dict(
            use_continuous_reading="boolean(default=True)",
            # 0: entire book, 1: current section, 2: current_page
            reading_mode="integer(default=0, min=0, max=2)",
            # 0: from cursor position, 1: from beginning of page
            start_reading_from="integer(default=0, max=1, min=0)",
            speak_page_number="boolean(default=False)",
            highlight_spoken_text="boolean(default=True)",
            select_spoken_text="boolean(default=False)",
            play_end_of_section_sound="boolean(default=True)",
        ),
    }

    def __post_init__(self):
        """Any initialization rutines go here."""

    def setup_event_handlers(self):
        """Set any event handlers for this service."""

    def shutdown(self):
        """Called when the app is about to exit."""

    def process_menubar(self, menubar):
        """Add items to the main menu."""

    def get_contextmenu(self):
        """Get items to add to  the content text control context menu."""
        return ()

    def get_settings_panels(self):
        return [
            # Translators: the label of a page in the settings dialog
            (10, "reading", ReadingPanel, _("Reading"),),
        ]

    def get_toolbar_items(self):
        """Return items to add to the application toolbar."""
        return ()

    def get_keyboard_shourtcuts(self):
        """Return a dictionary mapping control id's to keyboard shortcuts."""
        return {}


