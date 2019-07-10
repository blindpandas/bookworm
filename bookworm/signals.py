# coding: utf-8

"""
Implements the core signals of bookworm.
"""

from blinker import Namespace

# The namespace of bookworm signals
_signals = Namespace()


# Core app signals
app_started = _signals.signal("app/started")
app_shuttingdown = _signals.signal("app/shuttingdown")

# Book reader signals
reader_book_loaded = _signals.signal("reader/loaded")
reader_book_unloaded = _signals.signal("reader/unloaded")
reader_page_changed = _signals.signal("reader/page_changed")
reader_section_changed = _signals.signal("reader/section_changed")

# Configuration
config_updated = _signals.signal("config/updated")

# Miscellaneous signals
notes_export_completed = _signals.signal("note-export-completed")
speech_engine_state_changed = _signals.signal("speech-engine.state-changed")
