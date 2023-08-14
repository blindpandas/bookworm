# coding: utf-8

import functools
from enum import IntEnum, auto

SsmlIdentifier = type("SsmlIdentifier", (), {})


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
    # Decompose style
    start_voice = auto()
    end_voice = auto()
    start_emph = auto()
    end_emph = auto()
    start_prosody = auto()
    end_prosody = auto()


class EmphSpec(SsmlIdentifier, IntEnum):
    not_set = 0
    strong = 1
    moderate = 2
    null = 3
    reduced = 4

    @property
    def ssml_identifier(self):
        return self.ssml_string_map()[self]

    @staticmethod
    @functools.cache
    def ssml_string_map():
        return {
            EmphSpec.not_set: "",
            EmphSpec.null: "none",
            EmphSpec.strong: "strong",
            EmphSpec.moderate: "moderate",
            EmphSpec.reduced: "reduced",
        }


class VolumeSpec(SsmlIdentifier, IntEnum):
    not_set = 0
    silent = 1
    extra_soft = 2
    soft = 3
    medium = 4
    loud = 5
    extra_loud = 6
    default = 7

    @property
    def ssml_identifier(self):
        return self.ssml_string_map()[self]

    @staticmethod
    @functools.cache
    def ssml_string_map():
        return {
            VolumeSpec.not_set: "",
            VolumeSpec.silent: "silent",
            VolumeSpec.extra_soft: "x-soft",
            VolumeSpec.soft: "soft",
            VolumeSpec.medium: "medium",
            VolumeSpec.loud: "loud",
            VolumeSpec.extra_loud: "x-loud",
            VolumeSpec.default: "default",
        }


class RateSpec(SsmlIdentifier, IntEnum):
    not_set = 0
    extra_fast = 1
    fast = 2
    medium = 3
    slow = 4
    extra_slow = 5

    @property
    def ssml_identifier(self):
        return self.ssml_string_map()[self]

    @staticmethod
    @functools.cache
    def ssml_string_map():
        return {
            RateSpec.not_set: "",
            RateSpec.extra_fast: "x-fast",
            RateSpec.fast: "fast",
            RateSpec.medium: "medium",
            RateSpec.extra_slow: "x-slow",
            RateSpec.slow: "slow",
        }


class PauseSpec(SsmlIdentifier, IntEnum):
    null = 0
    extra_small = 1
    small = 2
    medium = 3
    large = 4
    extra_large = 5

    @property
    def ssml_identifier(self):
        return self.ssml_string_map()[self]

    @staticmethod
    @functools.cache
    def ssml_string_map():
        return {
            PauseSpec.null: "none",
            PauseSpec.extra_small: "x-weak",
            PauseSpec.small: "weak",
            PauseSpec.medium: "medium",
            PauseSpec.large: "strong",
            PauseSpec.extra_large: "x-strong",
        }
