# coding: utf-8

"""Constants for controlling speech."""

from System.Speech.Synthesis import (
    SynthesizerState,
    PromptEmphasis,
    PromptVolume,
    PromptRate,
    PromptBreak,
)
from enum import IntEnum, auto


class EngineEvent(IntEnum):
    bookmark_reached = auto()
    state_changed = auto()
    speech_progress = auto()


class SynthState(IntEnum):
    ready = SynthesizerState.Ready
    busy = SynthesizerState.Speaking
    paused = SynthesizerState.Paused


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
    not_set = PromptEmphasis.NotSet
    null = getattr(PromptEmphasis, "None")
    reduced = PromptEmphasis.Reduced
    moderate = PromptEmphasis.Moderate
    strong = PromptEmphasis.Strong


class VolumeSpec(IntEnum):
    not_set = PromptVolume.NotSet
    default = PromptVolume.Default
    silent = PromptVolume.Silent
    extra_soft = PromptVolume.ExtraSoft
    soft = PromptVolume.Soft
    medium = PromptVolume.Medium
    loud = PromptVolume.Loud
    extra_loud = PromptVolume.ExtraLoud


class RateSpec(IntEnum):
    not_set = PromptRate.NotSet
    extra_slow = PromptRate.ExtraSlow
    slow = PromptRate.Slow
    medium = PromptRate.Medium
    fast = PromptRate.Fast
    extra_fast = PromptRate.ExtraFast


class PauseSpec(IntEnum):
    null = getattr(PromptBreak, "None")
    extra_small = PromptBreak.ExtraSmall
    small = PromptBreak.Small
    medium = PromptBreak.Medium
    large = PromptBreak.Large
    extra_large = PromptBreak.ExtraLarge

