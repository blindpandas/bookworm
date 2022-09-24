# coding: utf-8

"""Constants for controlling speech."""

from enum import IntEnum, auto
from functools import cached_property


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

    @cached_property
    def ssml_string_map(self):
        return {
            self.not_set: "",
            self.null: "none",
            self.strong: "strong",
            self.moderate: "moderate",
            self.reduced: "reduced"
        }

class VolumeSpec(IntEnum):
    not_set = 0
    silent = 1
    extra_soft = 2
    soft = 3
    medium = 4
    loud = 5
    extra_loud = 6
    default = 7

    @cached_property
    def ssml_string_map(self):
        return {
            self.not_set: "",
            self.silent: "silent",
            self.extra_soft: "x-soft",
            self.soft: "soft",
            self.medium: "medium",
            self.loud: "loud",
            self.extra_loud: "x-loud",
            self.default: "default"
        }



class RateSpec(IntEnum):
    not_set = 0
    extra_fast = 1
    fast = 2
    medium = 3
    slow = 4
    extra_slow = 5

    @cached_property
    def ssml_string_map(self):
        return {
            self.not_set: "",
            self.extra_fast: "x-fast",
            self.fast: "fast",
            self.medium: "medium",
            self.extra_slow: "x-slow",
            self.slow: "slow"
        }


class PauseSpec(IntEnum):
    null = 0
    extra_small = 1
    small = 2
    medium = 3
    large = 4
    extra_large = 5

    @cached_property
    def ssml_string_map(self):
        return {
            self.null: "none",
            self.extra_small: "x-weak",
            self.small: "weak",
            self.medium: "medium",
            self.large: "strong",
            self.extra_large: "x-strong"
        }