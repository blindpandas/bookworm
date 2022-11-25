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
    include_page_label = boolean(default=False)
    show_reading_progress_percentage = boolean(default=True)
    use_continuous_reading = boolean(default=True)
[history]
    recent_terms = list(default=list())
    last_folder = string(default="")
    set_file_assoc = integer(default=0)
[appearance]
    apply_text_styles = boolean(default=True)
    start_maximized = boolean(default=False)
    use_opendyslexic_font = boolean(default=False)
    font_facename = string(default="")
    font_family = string(default="")
    font_point_size = integer(default=12)
    use_bold_font = boolean(default=False)
    text_view_margins = integer(default=50, min=0, max=100)
[advanced]
"""
)
