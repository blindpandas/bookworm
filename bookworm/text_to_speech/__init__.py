# coding: utf-8

from base64 import b64decode, b64encode
from collections import deque
from contextlib import contextmanager, suppress
from functools import cached_property

import msgpack
import wx
from pynput import keyboard

from bookworm import config
from bookworm import speech
from bookworm.logger import logger
from bookworm.resources import app_icons, sounds
from bookworm.service import BookwormService
from bookworm.signals import (
    _signals,
    app_started,
    config_updated,
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    reading_position_change,
)
from bookworm.speech_engines import TTS_ENGINES
from bookworm.speechdriver import DummySpeechEngine, speech_engine_state_changed
from bookworm.speechdriver.enumerations import (
    EmphSpec,
    EngineEvent,
    PauseSpec,
    SynthState,
)
from bookworm.speechdriver.utterance import SpeechStyle, SpeechUtterance
from bookworm.structured_text import TextInfo
from bookworm.utils import gui_thread_safe

from .tts_config import TTSConfigManager, tts_config_spec
from .tts_gui import (
    SPEECH_KEYBOARD_SHORTCUTS,
    ReadingPanel,
    SpeechMenu,
    SpeechPanel,
    StatefulSpeechMenuIds,
    StatelessSpeechMenuIds,
)

log = logger.getChild(__name__)

# Custom signals
should_auto_navigate_to_next_page = _signals.signal(
    "tts/should-auto-navigate-to-next-page"
)
restart_speech = _signals.signal("tts/restart-speech")

# Utterance types
UT_BEGIN = "ub"
UT_END = "ue"
UT_PARAGRAPH_BEGIN = "pb"
UT_PARAGRAPH_END = "pe"
UT_PAGE_BEGIN = "gb"
UT_PAGE_END = "ge"
UT_SECTION_BEGIN = "sb"
UT_SECTION_END = "se"

class TextToSpeechService(BookwormService):
    name = "text_to_speech"
    config_spec = tts_config_spec
    has_gui = True
    stateful_menu_ids = StatefulSpeechMenuIds
    __available_engines = TTS_ENGINES
    speech_engines = [e for e in __available_engines if e.check()]

    @classmethod
    def check(cls):
        return any(cls.speech_engines)

    def __post_init__(self):
        self.config_manager = TTSConfigManager()
        self.textCtrl = self.view.contentTextCtrl
        self.engine = None
        self.pynput_listener = None
        self.pynput_key_map = {
            keyboard.Key.media_play_pause: self.pause_or_resume,
            keyboard.Key.media_next: self.fastforward,
            keyboard.Key.media_previous: self.rewind,
        }
        self._whole_page_text_info = None
        self._highlighted_ranges = set()
        restart_speech.connect(self.on_restart_speech, sender=self.view)
        reader_book_unloaded.connect(self.on_reader_unload, sender=self.reader)
        reader_page_changed.connect(self._change_page_for_tts, sender=self.reader)
        # maintain state upon book load
        self.view.add_load_handler(
            lambda s: self.on_engine_state_changed(state=SynthState.ready)
        )
        reading_position_change.connect(
            self.on_reading_position_change, sender=self.view
        )
        config_updated.connect(self._on_config_updated)
        app_started.connect(self._on_app_started)
        self.initialize_state()

    def initialize_state(self):
        self.utterance_queue = deque()
        self.text_info = None
        self._whole_page_text_info = None
        self.clear_highlighted_ranges()

    def _on_app_started(self, sender):
        log.debug("App has started, setting up initial listener state.")
        self._update_listener_state()

    def shutdown(self):
        self.stop_global_listener()
        with suppress(RuntimeError):
            self.close()

    def _on_config_updated(self, sender, section=None):
        if section == "reading":
            log.debug("Reading config updated, toggling global listener.")
            self._update_listener_state()

    def _update_listener_state(self):
        enable = config.conf["reading"]["enable_global_media_keys"]
        if enable and self.pynput_listener is None:
            self.start_global_listener()
        elif not enable and self.pynput_listener is not None:
            self.stop_global_listener()

    def start_global_listener(self):
        if self.pynput_listener is None:
            try:
                self.pynput_listener = keyboard.Listener(on_press=self.on_key_press_global)
                self.pynput_listener.start()
            except Exception:
                self.pynput_listener = None

    def stop_global_listener(self):
        if self.pynput_listener:
            try:
                self.pynput_listener.stop()
                self.pynput_listener.join()
                self.pynput_listener = None
            except Exception:
                self.pynput_listener = None

    def on_key_press_global(self, key):
        action = self.pynput_key_map.get(key)
        if action:
            wx.CallAfter(action)
    
    def process_menubar(self, menubar):
        self.menu = SpeechMenu(self)
        # Translators: the label of an item in the application menubar
        return (20, self.menu, _("S&peech"))

    def get_settings_panels(self):
        return [
            # Translators: the label of a page in the settings dialog
            (10, "reading", ReadingPanel, _("Reading")),
            # Translators: the label of a page in the settings dialog
            (15, "speech", SpeechPanel, _("Voice")),
        ]

    def get_contextmenu_items(self):
        return ()

    def get_toolbar_items(self):
        return [
            (52, "rewind", _("Back"), StatefulSpeechMenuIds.rewind),
            (53, "play", _("Play"), StatefulSpeechMenuIds.playToggle),
            (54, "fastforward", _("Forward"), StatefulSpeechMenuIds.fastforward),
            (55, "profile", _("Voice"), StatelessSpeechMenuIds.voiceProfiles),
            (56, "", "", None),
        ]

    def get_keyboard_shortcuts(self):
        return SPEECH_KEYBOARD_SHORTCUTS

    def stop_speech(self, user_requested=False):
        self.initialize_state()
        self.engine.stop()
        if user_requested:
            setattr(self, "_requested_play", False)

    def encode_bookmark(self, data):
        payload = msgpack.dumps(data)
        return b64encode(payload).decode("ascii")

    def decode_bookmark(self, payload):
        data = b64decode(payload.encode("ascii"))
        return msgpack.loads(data)

    @contextmanager
    def queue_speech_utterance(self):
        utterance = SpeechUtterance()
        utterance.add_bookmark(self.encode_bookmark({"t": UT_BEGIN}))
        yield utterance
        utterance.add_text("\n.")
        utterance.add_bookmark(self.encode_bookmark({"t": UT_END}))
        self.utterance_queue.appendleft(utterance)

    def play_or_resume(self):
        if not self.is_engine_ready:
            self.initialize_engine()
        state = self.engine.state
        if state is SynthState.busy:
            wx.Bell()
            return
        if state is SynthState.paused:
            self.engine.resume()
            # Translators: a message that is announced when the speech is resumed
            speech.announce(_("Resumed"))
            return
        setattr(self, "_requested_play", True)
        self.speak_page()

    def pause_or_resume(self):
        if not self.is_engine_ready:
            wx.Bell()
            return
        state = self.engine.state
        if state is SynthState.busy:
            self.engine.pause()
            # Translators: a message that is announced when the speech is paused
            speech.announce(_("Paused"))
        elif state is SynthState.paused:
            self.engine.resume()
            # Translators: a message that is announced when the speech is resumed
            speech.announce(_("Resumed"))
        else:
            self.play_or_resume()

    def stop_playback(self):
        if self.is_engine_ready and self.engine.state is not SynthState.ready:
            self.stop_speech(user_requested=True)
            # Translators: a message that is announced when the speech is stopped
            speech.announce(_("Stopped"))
        else:
            wx.Bell()

    def fastforward(self):
        if not self.is_engine_ready or self.text_info is None:
            wx.Bell()
            return
        was_speaking = self.engine.state is SynthState.busy
        if was_speaking:
            self.engine.stop()
        insertion_point = self.view.get_insertion_point()
        try:
            p_range = self.text_info.get_paragraph_to_the_right_of(insertion_point)
            self.view.set_insertion_point(p_range.start)
            if was_speaking:
                self.initialize_state()
                self.speak_page(start_pos=p_range.start)
            else:
                sounds.navigation.play()
        except LookupError:
            wx.Bell()

    def rewind(self):
        if not self.is_engine_ready:
            wx.Bell()
            return
        was_speaking = self.engine.state is SynthState.busy
        if was_speaking:
            self.engine.stop()
        if self._whole_page_text_info is None:
            full_text = self.view.get_text_by_range(0, -1)
            self._whole_page_text_info = TextInfo(full_text)
        insertion_point = self.view.get_insertion_point()
        try:
            p_range = self._whole_page_text_info.get_paragraph_to_the_left_of(
                insertion_point
            )
            self.view.set_insertion_point(p_range.start)
            if was_speaking:
                self.initialize_state()
                self.speak_page(start_pos=p_range.start)
            else:
                sounds.navigation.play()
        except LookupError:
            wx.Bell()

    def on_restart_speech(self, sender, start_speech_from, speech_prefix=None):
        if (not self.is_engine_ready) or (self.engine.state is not SynthState.busy):
            return
        self.stop_speech()
        if speech_prefix:
            with self.queue_speech_utterance() as utterance:
                utterance.add_text(speech_prefix)
                utterance.add_pause(PauseSpec.extra_small)
        self.speak_page(start_pos=start_speech_from, init_state=False)

    def on_reader_unload(self, sender):
        self.close()

    def _change_page_for_tts(self, sender, current, prev):
        if not self.is_engine_ready:
            return
        self.initialize_state()
        self._whole_page_text_info = None
        if self.engine.state is not SynthState.ready:
            self.engine.stop()
        if getattr(self, "_requested_play", False):
            if config.conf["reading"]["speak_page_number"]:
                with self.queue_speech_utterance() as utterance:
                    utterance.add_text(
                        # Translators: a message to announce when navigating to another page
                        _("Page {page} of {total}").format(
                            page=self.reader.current_page + 1,
                            total=len(self.reader.document),
                        )
                    )
                    utterance.add_pause(PauseSpec.medium)
            self.speak_page(init_state=False)

    def configure_start_page_utterance(self, utterance, page):
        page_is_the_first_of_its_section = (
            page.is_first_of_section
            and (page.section.parent is not None)
            and (page.section.parent.is_root)
        )
        utterance.add_bookmark(
            self.encode_bookmark(
                {
                    "t": UT_PAGE_BEGIN,
                    "isf": page_is_the_first_of_its_section,
                }
            )
        )
        if page_is_the_first_of_its_section:
            utterance.add_bookmark(self.encode_bookmark({"t": UT_SECTION_BEGIN}))

    def configure_end_page_utterance(self, utterance, page):
        page_is_the_last_of_its_section = (
            not self.reader.document.is_single_page_document()
            and page.is_last_of_section
            and not page.section.has_children
        )
        if page.section.is_root:
            utterance.add_audio(sounds.section_end.path)
            # Translators: a message to speak at the end of the document
            utterance.add_audio(sounds.section_end.path)
            utterance.add_text(_("End of document."))
        if page_is_the_last_of_its_section:
            self.configure_end_of_section_utterance(utterance, page.section)
        else:
            utterance.add_pause(self.config_manager["end_of_page_pause"])
        utterance.add_bookmark(
            self.encode_bookmark(
                {
                    "t": UT_PAGE_END,
                    "isl": page_is_the_last_of_its_section,
                }
            )
        )
        utterance.add_pause(50)
        utterance.add_bookmark(self.encode_bookmark({"t": UT_SECTION_END}))

    def configure_end_of_section_utterance(self, utterance, section):
        if config.conf["reading"]["notify_on_section_end"]:
            utterance.add_audio(sounds.section_end.path)
            # Translators: a message to speak at the end of the chapter
            utterance.add_text(
                _("End of section: {chapter}.").format(chapter=section.title)
            )
        utterance.add_pause(self.config_manager["end_of_section_pause"])

    def speak_page(self, start_pos=None, init_state=True):
        if init_state:
            self.initialize_state()
        page = self.reader.get_current_page_object()
        if start_pos is None:
            start_pos = (
                0
                if config.conf["reading"]["start_reading_from"]
                else self.view.get_insertion_point()
            )
        text_content = self.view.get_text_by_range(start_pos, -1)
        self.text_info = text_info = TextInfo(
            text=f"{text_content}\n",
            lang=self.reader.document.language.two_letter_language_code,
            start_pos=start_pos,
        )
        if start_pos == 0:
            with self.queue_speech_utterance() as utterance:
                self.configure_start_page_utterance(utterance, page)
        self.add_text_utterances(text_info)
        with self.queue_speech_utterance() as utterance:
            self.configure_end_page_utterance(utterance, page)
        utterance.add_pause(PauseSpec.extra_small)
        if self.reader.document.is_single_page_document():
            # Translators: spoken message at the end of the document
            utterance.add_text(_("End of document"))
        self.engine.speak(self.utterance_queue.pop())

    def add_text_utterances(self, text_info):
        is_single_page_document = self.reader.document.is_single_page_document()
        _last_known_section = None
        parag_pause = self.config_manager["paragraph_pause"]
        sent_pause = self.config_manager["sentence_pause"]
        for paragraph, text_range in text_info.paragraphs:
            with self.queue_speech_utterance() as utterance:
                if is_single_page_document:
                    text_pos = sum(text_range.astuple()) / 2
                    sect = self.reader.document.get_section_at_position(text_pos)
                    if _last_known_section != sect:
                        if (_last_known_section is not None) and (
                            sect.parent is not _last_known_section
                        ):
                            self.configure_end_of_section_utterance(
                                utterance, sect.simple_prev
                            )
                        _last_known_section = sect
                utterance.add_bookmark(
                    self.encode_bookmark(
                        {
                            "t": UT_PARAGRAPH_BEGIN,
                            "txr": text_range.astuple(),
                        }
                    )
                )
                for sent in text_info.split_sentences(paragraph):
                    utterance.add_sentence(sent + " ")
                    utterance.add_pause(sent_pause)
                utterance.add_text("")
                utterance.add_pause(parag_pause)
                utterance.add_bookmark(
                    self.encode_bookmark(
                        {
                            "t": UT_PARAGRAPH_END,
                            "txr": text_range.astuple(),
                        }
                    )
                )

    @gui_thread_safe
    def process_bookmark(self, bookmark):
        bookmark_type = bookmark["t"]
        if bookmark_type == UT_END:
            try:
                next_utterance = self.utterance_queue.pop()
                self.engine.speak(next_utterance)
            except IndexError:
                return
        elif bookmark_type == UT_PARAGRAPH_BEGIN:
            p_start, p_end = bookmark["txr"]
            self.view.set_insertion_point(p_start)
            if config.conf["reading"]["highlight_spoken_text"]:
                self.view.highlight_range(p_start, p_end)
            if config.conf["reading"]["select_spoken_text"]:
                self.view.select_text(p_start, p_end)
            self._highlighted_ranges.add((p_start, p_end))
        elif bookmark_type == UT_PARAGRAPH_END:
            if config.conf["reading"]["highlight_spoken_text"]:
                self.view.clear_highlight(*bookmark["txr"])
            if config.conf["reading"]["select_spoken_text"]:
                self.view.unselect_text()
        elif bookmark_type == UT_PAGE_END:
            should_navigate = all(
                retval
                for func, retval in should_auto_navigate_to_next_page.send(self.view)
            )
            if not should_navigate:
                return
            is_last_of_section = bookmark["isl"]
            tts_reading_mode = config.conf["reading"]["reading_mode"]
            if tts_reading_mode < 2:
                if (tts_reading_mode == 1) and is_last_of_section:
                    return
                navigated = self.reader.go_to_next()
                if navigated:
                    self.speak_page()

    def initialize_engine(self):
        engine_name = self.config_manager["engine"]
        last_known_state = (
            SynthState.ready if not self.is_engine_ready else self.engine.state
        )
        if self.is_engine_ready and (self.engine.name == engine_name):
            self.configure_engine(last_known_state)
            return
        self.close()
        Engine = self.get_engine(engine_name)
        self.engine = Engine()
        # Event handlers
        self.engine.bind(EngineEvent.state_changed, self.on_state_changed)
        self.engine.bind(EngineEvent.bookmark_reached, self.on_bookmark_reached)
        self.configure_engine(last_known_state)
        self._try_set_tts_language()

    def configure_engine(self, last_known_state=SynthState.ready):
        if not self.is_engine_ready:
            return
        if self.engine.state is not SynthState.ready:
            self.engine.stop()
        try:
            self.engine.configure(self.config_manager)
        except ValueError:
            self.config_manager.restore_defaults()
            self.config_manager.save()
            if self.engine.get_first_available_voice() is None:
                self.reader.view.notify_user(
                    # Translators: the title of a message telling the user that no TTS voice found
                    _("No TTS Voices"),
                    # Translators: a message telling the user that no TTS voice found
                    _(
                        "A valid Text-to-speech voice was not found for the current speech engine.\n"
                        "Text-to-speech functionality will be disabled."
                    ),
                )
                return
        if self.reader.ready and last_known_state is SynthState.busy:
            self.speak_page()

    def _try_set_tts_language(self):
        if not config.conf["reading"]["ask_to_switch_voice_to_current_book_language"]:
            return
        if self.engine.voice.speaks_language(
            self.reader.document.language, strict=False
        ):
            return
        msg = wx.MessageBox(
            # Translators: a message telling the user that the TTS voice has been changed
            _(
                "Bookworm has noticed that the currently configured Text-to-speech voice "
                "speaks a language different from that of this document.\n"
                "Do you want to temporary switch to another voice that "
                "speaks a language similar to the language  of the currently opened document?"
                "\n\n"
                "Voice language: {voice_lang}\n"
                "Document language: {document_lang}"
            ).format(
                voice_lang=self.engine.voice.language.description,
                document_lang=self.reader.document.language.description,
            ),
            # Translators: the title of a message telling the user that the TTS voice has been changed
            _("Incompatible TTS Voice Detected"),
            parent=self.view,
            style=wx.YES_NO | wx.ICON_INFORMATION,
        )
        if msg == wx.NO:
            return
        lang = self.reader.document.language
        if (self.engine.voice is not None) and (
            not self.engine.voice.speaks_language(lang)
        ):
            voice_for_lang = self.engine.get_voices_by_language(lang)
            if voice_for_lang:
                self.engine.voice = voice_for_lang[0]

    def close(self):
        self.initialize_state()
        if self.engine is not None:
            self.engine.stop()
            self.engine.close()
            self.engine = None

    @property
    def is_engine_ready(self):
        return self.engine is not None

    def on_reading_position_change(self, sender, position, **kwargs):
        if (tts_speech_prefix := kwargs.get("tts_speech_prefix")) is not None:
            restart_speech.send(
                sender, start_speech_from=position, speech_prefix=tts_speech_prefix
            )

    def on_state_changed(self, sender, state):
        speech_engine_state_changed.send(self.view, service=self, state=state)
        self.on_engine_state_changed(state)

    def on_bookmark_reached(self, sender, bookmark):
        self.process_bookmark(self.decode_bookmark(bookmark))

    @gui_thread_safe
    def on_engine_state_changed(self, state):
        if state is SynthState.ready:
            self.clear_highlighted_ranges()
        if state is SynthState.busy:
            image = app_icons.pause
        else:
            image = app_icons.play
        self.view.toolbar.SetToolNormalBitmap(
            StatefulSpeechMenuIds.playToggle, image.GetBitmap()
        )
        if not self.reader.ready:
            return
        menu = self.menu
        toolbar = self.view.toolbar
        gui_state = {
            (StatefulSpeechMenuIds.pauseToggle, state is not SynthState.ready),
            (StatefulSpeechMenuIds.stop, state is not SynthState.ready),
            (StatefulSpeechMenuIds.play, state is not SynthState.busy),
            (StatefulSpeechMenuIds.fastforward, state is SynthState.busy),
            (StatefulSpeechMenuIds.rewind, state is SynthState.busy),
        }
        for ctrl_id, enable in gui_state:
            menu.Enable(ctrl_id, enable)
            toolbar.EnableTool(ctrl_id, enable)

    def clear_highlighted_ranges(self):
        self.view.unselect_text()
        for start_pos, stop_pos in self._highlighted_ranges:
            self.view.clear_highlight(start_pos, stop_pos)
        self._highlighted_ranges.clear()

    @classmethod
    def get_engine(cls, engine_name, first_available=True):
        engine = None
        for e in cls.speech_engines:
            if e.name == engine_name:
                engine = e
                break
        if engine is None:
            if first_available:
                return (
                    cls.speech_engines[0]
                    if any(cls.speech_engines)
                    else DummySpeechEngine
                )
            else:
                raise LookupError(f"Engine {engine_name} was not found or unavailable.")
        return engine
