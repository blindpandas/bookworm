# coding: utf-8

from io import StringIO



config_spec = StringIO(
    f"""
[general]
    language = string(default="default")
    announce_ui_messages = boolean(default=True)
    show_file_name_as_title = boolean(default=False)
    open_with_last_position = boolean(default=True)
    play_pagination_sound = boolean(default=True)
    play_page_note_sound = boolean(default=True)
    highlight_bookmarked_positions = boolean(default=True)
    auto_check_for_updates = boolean(default=True)
    last_update_check = integer(default=0)
[history]
    recently_opened = list(default=list())
    recent_terms = list(default=list())
    last_folder = string(default="")
    set_file_assoc = integer(default=0)
"""
)


