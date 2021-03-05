# coding: utf-8

from io import StringIO


config_spec = StringIO(
    f"""
[general]
    language = string(default="default")
    announce_ui_messages = boolean(default=True)
    show_file_name_as_title = boolean(default=False)
    open_with_last_position = boolean(default=True)
    auto_check_for_updates = boolean(default=True)
    last_update_check = float(default=0)
    play_pagination_sound = boolean(default=True)
    speak_page_number = boolean(default=True)
    speak_section_title = boolean(default=True)
    include_page_label = boolean(default=False)
[history]
    recently_opened = list(default=list())
    recent_terms = list(default=list())
    last_folder = string(default="")
    set_file_assoc = integer(default=0)
"""
)
