# coding: utf-8

"""Constants for controlling speech."""

from enum import IntEnum, auto


class EngineEvent(IntEnum):
    bookmark_reached = auto()
    state_changed = auto()
    speech_progress = auto()


class SynthState(IntEnum):
    ready = 0
    busy = 1
    paused = 2


class SpeechElementKind(IntEnum):
    """Represent the kind of a speech element."""

    text = auto()
    ssml = auto()
    sentence = auto()
    bookmark = auto()
    pause = auto()
    audio = auto()
    start_paragraph = auto()
    end_paragraph = auto()
    start_style = auto()
    end_style = auto()


class EmphSpec(IntEnum):
    not_set = 0
    strong = 1
    moderate = 2
    null = 3
    reduced = 4


class VolumeSpec(IntEnum):
    not_set = 0
    silent = 1
    extra_soft = 2
    soft = 3
    medium = 4
    loud = 5
    extra_loud = 6
    default = 7


class RateSpec(IntEnum):
    not_set = 0
    extra_fast = 1
    fast = 2
    medium = 3
    slow = 4
    extra_slow = 5


class PauseSpec(IntEnum):
    null = 0
    extra_small = 1
    small = 2
    medium = 3
    large = 4
    extra_large = 5
