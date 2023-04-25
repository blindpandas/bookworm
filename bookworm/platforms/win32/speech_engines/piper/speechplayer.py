# coding: utf-8

import time
import typing
import queue
import struct
import threading
import logging

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager
from dataclasses import dataclass
from enum import IntEnum

from . import nvwave
from .opentts_abc import TextToSpeechSystem, BaseResult, AudioResult, MarkResult
from .opentts_abc.ssml import SSMLSpeaker



log = logging.getLogger(__name__)

STOP_PLAYBACK = object()


# Sentinel
_missing = object()


class PlayerState(IntEnum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


@dataclass
class PiperSpeechPlayer(AbstractContextManager):
    tts: TextToSpeechSystem
    state_change_callback: typing.Optional[typing.Callable[PlayerState, None]] = None
    bookmark_callback: typing.Optional[typing.Callable[str, None]] = None

    def __post_init__(self):
        self.ssml_speaker = SSMLSpeaker(self.tts)
        self._players = {}
        self._players_lock = threading.RLock()
        self.result_queue = queue.Queue()
        self._speech_task_executor = ThreadPoolExecutor(thread_name_prefix="piper_tts")
        self.playing_thread = threading.Thread(target=self.player_func)
        self.playing_thread.daemon = True
        self.playing_thread.start()
        self.__current_state = PlayerState.STOPPED
        self._pause_playing = threading.Event()
        self._continue_playback = threading.Event()

    def close(self):
        self.stop()
        self.tts.shutdown()
        self._speech_task_executor.shutdown(wait=False)
        self._players.clear()

    def __del__(self):
        self.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _get_or_create_player(self, sampling_rate, bits_per_sample, channels, output_device=_missing):
        key = (sampling_rate, bits_per_sample, channels)
        if key not in self._players:
            kwargs = {
                "channels": channels,
                "samplesPerSec": sampling_rate,
                "bitsPerSample": bits_per_sample,
                "buffered": True
            }
            if output_device is not _missing:
                kwargs["outputDevice"] = output_device
            self._players[key] = nvwave.WavePlayer(**kwargs)
        return self._players[key] 

    def get_state(self) -> PlayerState:
        return self.__current_state

    def set_state(self, new_state):
        if self.__current_state is new_state:
            return
        self.__current_state = new_state
        if self.state_change_callback is not None:
            self.state_change_callback(new_state)

    def speak_ssml(self, ssml):
        self._speech_task_executor.submit(self._do_speak_ssml, ssml)
        #self._do_speak_ssml(ssml)

    def stop(self):
        if not self._continue_playback.is_set():
            return
        with self._players_lock:
            for nvwp in self._players.values():
                nvwp.stop()
        with self.result_queue.mutex:
            self.result_queue.queue.clear()
        self.result_queue.put_nowait(STOP_PLAYBACK)

    def pause(self):
        if not self._pause_playing.is_set():
            return
        with self._players_lock:
            for nvwp in self._players.values():
                nvwp.pause(True)
        self._pause_playing.clear()
        self.set_state(PlayerState.PAUSED)

    def resume(self):
        if self._pause_playing.is_set():
            return
        with self._players_lock:
            for nvwp in self._players.values():
                nvwp.pause(False)
        self._pause_playing.set()
        self.set_state(PlayerState.PLAYING)

    def _do_speak_ssml(self, ssml):
        if self._continue_playback.is_set():
            self.stop()
        self.result_queue = queue.Queue()
        self._pause_playing.set()
        self._continue_playback.set()
        self.set_state(PlayerState.PLAYING)
        for res in self.ssml_speaker.speak(ssml):
            self._pause_playing.wait()
            if not self._continue_playback.is_set():
                return
            self.result_queue.put_nowait(res)
        self.result_queue.put_nowait(STOP_PLAYBACK)

    def player_func(self):
        while True:
            try:
                item = self.result_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if item is STOP_PLAYBACK:
                self.set_state(PlayerState.STOPPED)
                with self._players_lock:
                    self._players.clear()
                self._continue_playback.clear()
                self._continue_playback.wait()
                continue
            elif isinstance(item, AudioResult):
                player = self._get_or_create_player(
                    sampling_rate=item.sample_rate_hz,
                    bits_per_sample=item.sample_width_bytes*8,
                    channels=item.num_channels
                )
                player.feed(item.audio_bytes)
                player.idle()
            elif (self.bookmark_callback is not None) and isinstance(item, MarkResult):
                self.bookmark_callback(item.name)
