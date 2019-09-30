# coding: utf-8

from io import StringIO


# Some useful constants
PARAGRAPH_PAUSE_MAX = 5000
END_OF_PAGE_PAUSE_MAX = 7000
END_OF_SECTION_PAUSE_MAX = 9000


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
[history]
    recently_opened = list(default=list())
    recent_terms = list(default=list())
    last_folder = string(default="")
    set_file_assoc = integer(default=0)
[speech]
    engine = string(default="sapi")
    voice = string(default="")
    rate = integer(default=50)
    volume = integer(default=75)
    sentence_pause = integer(default=0, min=0, max={PARAGRAPH_PAUSE_MAX})
    paragraph_pause = integer(default=300, min=0, max={PARAGRAPH_PAUSE_MAX})
    end_of_page_pause = integer(default=500, min=0, max={END_OF_PAGE_PAUSE_MAX})
    end_of_section_pause = integer(default=900, min=0, max={END_OF_SECTION_PAUSE_MAX})
[reading]
    # 0: entire book, 1: current section, 2: current_page
    reading_mode = integer(default=0, min=0, max=2)
    # 0: from cursor position, 1: from beginning of page
    start_reading_from_ = integer(default=0, max=1, min=0)
    speak_page_number = boolean(default=False)
    highlight_spoken_text = boolean(default=True)
    select_spoken_text = boolean(default=False)
    play_end_of_section_sound = boolean(default=True)
"""
)


builtin_voice_profiles = [
    (
        # Translators: the name of a built-in voice profile
        _("Human-like"),
        dict(
            rate=60,
            sentence_pause=250,
            paragraph_pause=500,
            end_of_page_pause=700,
            end_of_section_pause=900,
        ),
    ),
    (
        # Translators: the name of a built-in voice profile
        _("Deep Reading"),
        dict(
            rate=60,
            sentence_pause=400,
            paragraph_pause=800,
            end_of_page_pause=1000,
            end_of_section_pause=2500,
        ),
    ),
    (
        # Translators: the name of a built-in voice profile
        _("Expresse"),
        dict(
            rate=65,
            sentence_pause=0,
            paragraph_pause=300,
            end_of_page_pause=500,
            end_of_section_pause=700,
        ),
    ),
]
