# coding: utf-8

import gc
from queue import PriorityQueue
from accessible_output2.outputs.auto import Auto
from bookworm import config
from bookworm.signals import (
    app_shuttingdown,
    config_updated,
    speech_engine_state_changed,
)
from bookworm.logger import logger
from .engines.sapi import SapiSpeechEngine
from .engines.onecore import OcSpeechEngine
from .enumerations import EngineEvent, SynthState
from .engines.sapi import SapiSpeechEngine




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

    speech_engines = (SapiSpeechEngine, OcSpeechEngine)

    def __init__(self, reader):
        self.reader = reader
        self.queue = PriorityQueue()
        self.engine = None
        app_shuttingdown.connect(lambda s: self.close(), weak=False)
        config_updated.connect(self.on_config_changed)

    def initialize_engine(self, engine_name=None):
        if self.is_ready:
            if self.engine.name == engine_name:
                return
            else:
                self.close()
        Engine = self.get_engine(engine_name)
        self.engine = Engine(language=self.reader.document.language)
        self.configure_engine()
        # Event handlers
        self.engine.bind(EngineEvent.state_changed, self.on_state_changed)
        self.engine.bind(EngineEvent.bookmark_reached, self.on_bookmark_reached)
        self._try_set_tts_language()

    def _try_set_tts_language(self):
        lang = self.reader.document.language
        if not self.engine.voice.speaks_language(lang):
            voice_for_lang = self.engine.get_voices_by_language(
                self.reader.document.language
            )
            if voice_for_lang:
                self.engine.voice = voice_for_lang[0]
                self.reader.view.notify_user(
                    # Translators: the title of a message telling the user that the TTS voice has been changed
                    _("Incompatible TTS Voice Detected"),
                    # Translators: a message telling the user that the TTS voice has been changed
                    _(
                        "Bookworm has noticed that the currently configured Text-to-speech voice "
                        "speaks a language different from that of this book. "
                        "Because of this, Bookworm has temporary switched to "
                        "another voice that speaks a language similar to the language  of this book."
                    ),
                )

    def close(self):
        if self.engine:
            self.engine.close()
            self.engine = None
            # Force a collection here to dispose of any stale  objects
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
            if self.is_ready and should_reconfig:
                self.initialize_engine()
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
        try:
            self.engine.set_voice_from_string(configured_voice)
        except ValueError:
            log.debug(f"Can not set voice to {configured_voice}")
            first_voice = self.engine.get_first_available_voice(
              self.reader.document.language
            )
            if first_voice is None:
                self.reader.view.notify_user(
                    # Translators: the title of a message telling the user that no TTS voice found
                  _("No TTS Voices"),
                  # Translators: a message telling the user that no TTS voice found
                  _(
                      "A valid Text-to-speech voice was not found on your computer.\n"
                      "Text-to-speech functionality will be disabled."
                    ),
                )
                return self.close()
            conf["voice"] = first_voice.id
            config.save()
            return self.configure_engine()
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

    def on_state_changed(self, state):
        speech_engine_state_changed.send(self, state=state)

    def on_bookmark_reached(self, bookmark):
        self.reader.process_bookmark(bookmark)

    @classmethod
    def get_engine(cls, engine_name=None):
        engine_name = engine_name or config.conf["speech"]["engine"]
        match = [e for e in cls.speech_engines if e.name == engine_name]
        if match:
            return match[0]
        raise ValueError(f"Unknown speech engine `{engine_name}`")
