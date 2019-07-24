# coding: utf-8

import gc
import System
from queue import PriorityQueue
from accessible_output2.outputs.auto import Auto
from bookworm import config
from bookworm.signals import (
    app_shuttingdown,
    config_updated,
    speech_engine_state_changed,
)
from bookworm.logger import logger
from .engine import SpeechEngine
from .enumerations import SynthState

log = logger.getChild(__name__)


_auto_output = None


def announce(message, urgent=True):
    """Speak and braille a message related to UI."""
    global _auto_output
    if not config.conf["general"]["announce_ui_messages"]:
        return
    if _auto_output is None:
        _auto_output = Auto()
    _auto_output.speak(message, interrupt=urgent)
    _auto_output.braille(message)


class SpeechProvider:
    """Text-to-speech controller for bookworm."""

    def __init__(self, reader):
        self.reader = reader
        self.queue = PriorityQueue()
        self.engine = None

    def initialize(self):
        if self.engine is not None:
            return
        self.engine = SpeechEngine(language=self.reader.document.language)
        self.configure_engine()
        # Event handlers
        app_shuttingdown.connect(lambda s: self.close(), weak=False)
        config_updated.connect(self.on_config_changed)
        # self.engine.SpeakProgress += self.on_speech_progress
        self.engine.StateChanged += self.on_state_changed
        self.engine.BookmarkReached += self.on_bookmark_reached
        self._try_set_tts_language()

    def _try_set_tts_language(self):
        lang = self.reader.document.language
        if not self.engine.get_current_voice().speaks_language(lang):
            voice_for_lang = self.reader.tts.engine.get_voices(
                self.reader.document.language
            )
            if voice_for_lang:
                self.engine.SelectVoice(voice_for_lang[0].name)
                self.reader.notify_user(
                    "Incompatible TTS Voice Detected",
                    "Bookworm has noticed that the currently configured Text-to-speech voice "
                    "speaks a language different from that of this book. "
                    "Because of this, Bookworm has temporary switched to "
                    "another voice that speaks a language similar to the language  of this book.",
                )

    def close(self):
        if self.engine:
            # Unsubscribe
            # self.engine.SpeakProgress -= self.on_speech_progress
            self.engine.StateChanged -= self.on_state_changed
            self.engine.BookmarkReached -= self.on_bookmark_reached
            self.engine.close()
            self.engine = None
            # Force a collection here to dispose of the .NET object
            gc.collect()

    def __del__(self):
        self.close()

    def on_config_changed(self, sender, section):
        if section == "speech":
            should_reconfig = False
            if config.conf.active_profile is None:
                if "name" not in sender.config.main:
                    should_reconfig = True
            elif ("name" in sender.config.main) and (
                config.conf.active_profile["name"] == sender.config.main["name"]
            ):
                should_reconfig = True
            if should_reconfig:
                self.configure_engine()
            if sender is not None:
                sender.reconcile()

    def configure_engine(self):
        if not self.is_ready:
            return
        state = self.engine.state
        if state is not SynthState.ready:
            self.engine.stop()
        conf = config.conf["speech"]
        configured_voice = conf["voice"]
        if configured_voice:
            try:
                self.engine.voice = configured_voice
            except ValueError:
                log.debug(f"Can not set voice to {configured_voice}")
                configured_voice = self.engine.get_first_available_voice(
                    self.reader.document.language
                )
                if configured_voice is None:
                    self.reader.notify_user(
                        "No TTS Voices",
                        "A valid Text-to-speech voice was not found on your computer.\n"
                        "Text-to-speech functionality will be disabled.",
                    )
                    conf["voice"] = ""
                    config.save()
                    return self.close()
            self.engine.voice = configured_voice
            conf["voice"] = configured_voice
            config.save()
        self.engine.rate = conf["rate"]
        self.engine.volume = conf["volume"]
        if self.reader.ready and state is SynthState.busy:
            self.reader.speak_current_page()

    def enqueue(self, utterance):
        if not self.is_ready:
            raise RuntimeError("Not initialized.")
        self.queue.put_nowait(utterance)

    def process_queue(self):
        if not self.is_ready:
            raise RuntimeError("Not initialized.")
        while not self.queue.empty():
            utterance = self.queue.get_nowait()
            self.engine.speak(utterance)

    @property
    def is_ready(self):
        return self.engine is not None

    def on_speech_progress(self, sender, args):
        pos = args.CharacterPosition
        count = args.CharacterCount
        log.debug(f"Position: {pos}, Count: {count}")

    def on_state_changed(self, sender, args):
        state = SynthState(args.State)
        speech_engine_state_changed.send(self, state=state)

    def on_bookmark_reached(self, sender, args):
        self.reader.process_bookmark(args.Bookmark)
