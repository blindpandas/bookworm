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
        # Holds the pynput listener instance for global media key control.
        # It runs in a separate thread.
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
        self._speech_session = getattr(self, "_speech_session", 0) + 1
        self._pause_on_speech_start = False
        self.utterance_queue = deque()
        self.text_info = None
        self._whole_page_text_info = None
        self.clear_highlighted_ranges()

    def _on_app_started(self, sender):
        log.debug("App has started, setting up initial listener state.")
        self.config_manager.restore_active_profile()
        self.menu.Enable(
            StatelessSpeechMenuIds.deactivateActiveVoiceProfile,
            self.config_manager.active_profile is not None,
        )
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
                log.info("Attempting to start global media key listener.")
                self.pynput_listener = keyboard.Listener(
                    on_press=self.on_key_press_global
                )
                self.pynput_listener.start()
            except Exception:
                log.exception("Failed to start the pynput global listener.")
                self.pynput_listener = None

    def stop_global_listener(self):
        if self.pynput_listener:
            try:
                log.info("Stopping global media key listener.")
                self.pynput_listener.stop()
                self.pynput_listener.join()
                self.pynput_listener = None
            except Exception:
                log.exception("Failed to stop the pynput global listener.")
                self.pynput_listener = None

    def on_key_press_global(self, key):
        action = self.pynput_key_map.get(key)
        if action:
            # CRITICAL: This method is called from a non-GUI thread created by pynput.
            # Any direct interaction with wxPython GUI elements or methods that
            # are not thread-safe MUST be delegated to the main GUI thread.
            # wx.CallAfter is the standard, safe way to do this.
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
        self.engine.stop()
        self.initialize_state()
        if user_requested:
            setattr(self, "_requested_play", False)

    def encode_bookmark(self, data):
        payload = msgpack.dumps({**data, "s": self._speech_session})
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
        if not self.is_engine_ready:
            wx.Bell()
            return
        state = self.engine.state
        if state is SynthState.busy:
            wx.Bell()
            return
        if state is SynthState.paused:
            self._pause_on_speech_start = False
            self.engine.resume()
            # Translators: a message that is announced when the speech is resumed
            speech.announce(_("Resumed"))
            return
        if getattr(self, "_requested_play", False):
            if self._pause_on_speech_start:
                self._pause_on_speech_start = False
                if self.engine.state is SynthState.paused:
                    self.engine.resume()
                # Translators: a message that is announced when the speech is resumed
                speech.announce(_("Resumed"))
            else:
                wx.Bell()
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
            self._pause_on_speech_start = False
            self.engine.resume()
            # Translators: a message that is announced when the speech is resumed
            speech.announce(_("Resumed"))
        elif getattr(self, "_requested_play", False):
            pause_requested = not self._pause_on_speech_start
            self._pause_on_speech_start = pause_requested
            if pause_requested and self.engine.state is SynthState.busy:
                self._pause_on_speech_start = False
                self.engine.pause()
            elif (
                not pause_requested and self.engine.state is SynthState.paused
            ):
                self.engine.resume()
            # Translators: a message announced when pending speech is paused or resumed
            speech.announce(_("Paused") if pause_requested else _("Resumed"))
        else:
            self.play_or_resume()

    def stop_playback(self):
        if self.is_engine_ready and (
            self.engine.state is not SynthState.ready
            or getattr(self, "_requested_play", False)
        ):
            self.stop_speech(user_requested=True)
            # Translators: a message that is announced when the speech is stopped
            speech.announce(_("Stopped"))
        else:
            wx.Bell()

    def fastforward(self):
        self._seek_paragraph(forward=True)

    def rewind(self):
        self._seek_paragraph(forward=False)

    def _seek_paragraph(self, *, forward):
        if not self.is_engine_ready or (forward and self.text_info is None):
            wx.Bell()
            return
        previous_state = self.engine.state
        was_reading = previous_state is not SynthState.ready or getattr(
            self, "_requested_play", False
        )
        was_paused = previous_state is SynthState.paused or getattr(
            self, "_pause_on_speech_start", False
        )
        text_info = self.text_info
        if not forward:
            if self._whole_page_text_info is None:
                full_text = self.view.get_text_by_range(0, -1)
                self._whole_page_text_info = TextInfo(f"{full_text}\n")
            text_info = self._whole_page_text_info
        insertion_point = self.view.get_insertion_point()
        try:
            get_paragraph = (
                text_info.get_paragraph_to_the_right_of
                if forward
                else text_info.get_paragraph_to_the_left_of
            )
            target_position = get_paragraph(insertion_point).start
        except LookupError:
            step = 1 if forward else -1
            if self.reader.current_page + step not in self.reader.document:
                wx.Bell()
                return
            if was_reading:
                self.stop_speech()
            self._requested_play = False
            navigate = self.reader.go_to_next if forward else self.reader.go_to_prev
            if not navigate():
                wx.Bell()
                return
            full_text = self.view.get_text_by_range(0, -1)
            page_text_info = TextInfo(f"{full_text}\n")
            paragraphs = page_text_info.paragraphs
            target_position = (
                paragraphs[0 if forward else -1][1].start if paragraphs else 0
            )
        else:
            if was_reading:
                self.stop_speech()
        self.view.set_insertion_point(target_position)
        if not was_reading:
            self._requested_play = False
            sounds.navigation.play()
            return
        self._requested_play = True
        self._pause_on_speech_start = was_paused
        self.speak_page(start_pos=target_position, init_state=False)

    def on_restart_speech(self, sender, start_speech_from, speech_prefix=None):
        if not self.is_engine_ready or not getattr(self, "_requested_play", False):
            return
        was_paused = self.engine.state is SynthState.paused or getattr(
            self, "_pause_on_speech_start", False
        )
        self.stop_speech()
        if speech_prefix:
            with self.queue_speech_utterance() as utterance:
                utterance.add_text(speech_prefix)
                utterance.add_pause(PauseSpec.extra_small)
        self._pause_on_speech_start = was_paused
        self.speak_page(start_pos=start_speech_from, init_state=False)

    def on_reader_unload(self, sender):
        self.close()
        self._requested_play = False

    def _change_page_for_tts(self, sender, current, prev):
        if not self.is_engine_ready:
            return
        previous_state = self.engine.state
        was_paused = previous_state is SynthState.paused or getattr(
            self, "_pause_on_speech_start", False
        )
        if previous_state is not SynthState.ready or getattr(
            self, "_requested_play", False
        ):
            self.engine.stop()
        self.initialize_state()
        self._whole_page_text_info = None
        if getattr(self, "_requested_play", False):
            self._pause_on_speech_start = was_paused
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
            and not page.section.is_root
            and not page.section.has_children
        )
        if page_is_the_last_of_its_section:
            self.configure_end_of_section_utterance(utterance, page.section)
        else:
            utterance.add_pause(self.config_manager["end_of_page_pause"])
        if page.index == len(self.reader.document) - 1:
            utterance.add_audio(sounds.section_end.path)
            # Translators: a message to speak at the end of the document
            utterance.add_text(_("End of document."))
        utterance.add_bookmark(
            self.encode_bookmark(
                {
                    "t": UT_PAGE_END,
                    "isl": page_is_the_last_of_its_section,
                }
            )
        )

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
                    if _last_known_section is not sect:
                        if (_last_known_section is not None) and (
                            sect.parent is not _last_known_section
                        ):
                            self.configure_end_of_section_utterance(
                                utterance, _last_known_section
                            )
                            utterance.add_bookmark(
                                self.encode_bookmark({"t": UT_SECTION_END})
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
        if bookmark.get("s") != self._speech_session:
            return
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
                self._highlighted_ranges.add((p_start, p_end))
            if config.conf["reading"]["select_spoken_text"]:
                self.view.select_text(p_start, p_end)
        elif bookmark_type == UT_PARAGRAPH_END:
            text_range = tuple(bookmark["txr"])
            if text_range in self._highlighted_ranges:
                self.view.clear_highlight(*text_range)
                self._highlighted_ranges.discard(text_range)
            if config.conf["reading"]["select_spoken_text"]:
                self.view.unselect_text()
        elif bookmark_type == UT_PAGE_END:
            should_navigate = all(
                retval
                for func, retval in should_auto_navigate_to_next_page.send(self.view)
            )
            if not should_navigate:
                self._requested_play = False
                return
            is_last_of_section = bookmark["isl"]
            tts_reading_mode = config.conf["reading"]["reading_mode"]
            if tts_reading_mode >= 2 or (
                tts_reading_mode == 1 and is_last_of_section
            ):
                self._requested_play = False
                return
            if not self.reader.go_to_next():
                self._requested_play = False
        elif bookmark_type == UT_SECTION_END:
            if config.conf["reading"]["reading_mode"] == 1:
                self.stop_speech(user_requested=True)

    def initialize_engine(self):
        engine_name = self.config_manager["engine"]
        last_known_state = (
            SynthState.ready if not self.is_engine_ready else self.engine.state
        )
        was_reading = last_known_state is not SynthState.ready or getattr(
            self, "_requested_play", False
        )
        was_paused = last_known_state is SynthState.paused or getattr(
            self, "_pause_on_speech_start", False
        )
        reuse_engine = self.is_engine_ready and self.engine.name == engine_name
        if not reuse_engine:
            # Close any currently active engine before initializing a new one.
            if self.is_engine_ready:
                self.close()
            # Attempt to load the user's configured speech engine first.
            try:
                Engine = self.get_engine(engine_name, by_name=True)
                self.engine = Engine()
                log.info(f"Successfully initialized speech engine: {engine_name}")
            except Exception:
                # If the primary engine fails, try to find a working fallback.
                log.exception(
                    f"Failed to initialize the selected speech engine '{engine_name}'. Finding a working fallback.",
                    exc_info=True,
                )
                try:
                    FallbackEngine = self.get_engine(by_name=False)
                    self.engine = FallbackEngine()
                    log.info(
                        f"Successfully fell back to and initialized speech engine: {FallbackEngine.name}"
                    )
                    self.config_manager["engine"] = FallbackEngine.name
                    self.config_manager.save()
                    # Translators: The title of a warning dialog shown when an engine fails.
                    title = _("Speech Engine Warning")
                    # Translators: Explains that Bookworm selected a working fallback engine.
                    message = _(
                        "The previously selected speech engine could not be loaded. Bookworm has automatically switched to '{engine_display_name}'."
                    ).format(engine_display_name=_(FallbackEngine.display_name))
                    wx.CallAfter(
                        self.view.notify_user, title, message, icon=wx.ICON_WARNING
                    )
                except Exception:
                    # If even the fallback engine fails, disable TTS functionality completely.
                    log.exception(
                        "CRITICAL: No speech engines could be successfully initialized.",
                        exc_info=True,
                    )
                    self.engine = None
                    # Translators: The title of a critical error dialog.
                    title = _("Critical Speech Error")
                    # Translators: Explains that no speech engine could be loaded.
                    message = _(
                        "No speech engines could be loaded on this system. Text-to-speech functionality will be disabled."
                    )
                    wx.CallAfter(
                        self.view.notify_user, title, message, icon=wx.ICON_ERROR
                    )
                    self._requested_play = False
                    self._pause_on_speech_start = False
                    return
            # If an engine was successfully loaded, bind its events.
            self.engine.bind(EngineEvent.state_changed, self.on_state_changed)
            self.engine.bind(EngineEvent.bookmark_reached, self.on_bookmark_reached)
        if not self.configure_engine():
            self.close()
            self._requested_play = False
            return
        if self.reader.ready:
            self._try_set_tts_language()
        if self.reader.ready and was_reading:
            self._requested_play = True
            self._pause_on_speech_start = was_paused
            self.speak_page(init_state=False)

    def configure_engine(self):
        if not self.is_engine_ready:
            return False
        if self.engine.state is not SynthState.ready or getattr(
            self, "_requested_play", False
        ):
            self.engine.stop()
            self.initialize_state()
        try:
            self.engine.configure(self.config_manager)
        except ValueError:
            self.config_manager.restore_defaults()
            self.config_manager.save()
        if (
            self.engine.voice is None
            and self.engine._get_first_available_voice() is None
        ):
            self.reader.view.notify_user(
                # Translators: the title of a message telling the user that no TTS voice found
                _("No TTS Voices"),
                # Translators: a message telling the user that no TTS voice found
                _(
                    "A valid Text-to-speech voice was not found for the current speech engine.\n"
                    "Text-to-speech functionality will be disabled."
                ),
            )
            return False
        return True

    def _try_set_tts_language(self):
        if not config.conf["reading"]["ask_to_switch_voice_to_current_book_language"]:
            return
        voice = self.engine.voice
        if voice is None or voice.speaks_language(
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
        if self.engine is not None:
            self.engine.stop()
            self.engine.close()
            self.engine = None
        self.initialize_state()

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
        if state is SynthState.busy and self._pause_on_speech_start:
            self._pause_on_speech_start = False
            self.engine.pause()

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
    def get_engine(cls, engine_name="", by_name=True):
        """
        Gets a speech engine class based on the specified mode.

        This method has two modes of operation controlled by the 'by_name' parameter:
        1.  Precise Lookup (by_name=True): Finds the engine with the exact name provided.
        2.  Fallback/Availability Check (by_name=False): Finds the first engine in the
            list that can be successfully initialized.

        Args:
            engine_name (str): The name of the engine to find. Only used when by_name is True.
            by_name (bool): If True, performs a precise search by name. If False, finds the
                            first available and working engine.

        Returns:
            A subclass of BaseSpeechEngine that is ready to be instantiated. If no engine
            can be found or initialized, returns the DummySpeechEngine.

        Raises:
            LookupError: If by_name is True and no engine with the specified name is found.
        """
        if by_name:
            if engine_name == "sapi":
                # --- Backward Compatibility Fix ---
                # Handle old configuration files where the SAPI5 engine was named "sapi".
                engine_name= "sapi5"
            for e in cls.speech_engines:
                if e.name == engine_name:
                    return e
            # If no match is found in precise mode, it's an error condition.
            raise LookupError(f"Engine '{engine_name}' was not found.")
        else:
            # --- Fallback Mode ---
            # Find the first available engine by attempting to initialize each one.
            for Engine in cls.speech_engines:
                try:
                    temp_engine = Engine()
                    temp_engine.close()
                    # If no exception was raised, this engine is working.
                    return Engine
                except Exception:
                    # This engine failed to initialize (e.g., due to missing system
                    # components like for OneCore). Log it and try the next one.
                    log.warning(f"Fallback check failed for engine: {Engine.name}", exc_info=True)
                    continue
            # If the loop completes without finding any working engine,
            # return the DummySpeechEngine as the ultimate fallback.
            return DummySpeechEngine
