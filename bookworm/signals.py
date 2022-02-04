# coding: utf-8

"""
Implements the core signals of bookworm.
"""

from blinker import Namespace

# The namespace of bookworm signals
_signals = Namespace()


# Core app signals
app_booting = _signals.signal("app/booting")
app_starting = _signals.signal("app/starting")
app_started = _signals.signal("app/started")
app_window_shown = _signals.signal("app/window_shown")
app_shuttingdown = _signals.signal("app/shuttingdown")

# Book reader signals
reader_book_loaded = _signals.signal("reader/loaded")
reader_book_unloaded = _signals.signal("reader/unloaded")
reader_page_changed = _signals.signal("reader/page_changed")
reader_section_changed = _signals.signal("reader/section_changed")

# Configuration
config_updated = _signals.signal("config/updated")

# Reading position
reading_position_change = _signals.signal("caret/location_change")


# Local web server
local_server_booting = _signals.signal("local_server/booting")
