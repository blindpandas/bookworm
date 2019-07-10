# coding: utf-8

"""Constants for controlling speech."""

from System.Speech.Synthesis import (
    SynthesizerState,
    PromptEmphasis,
    PromptVolume,
    PromptRate,
    PromptBreak,
)
from enum import IntEnum


class SynthState(IntEnum):
    ready = SynthesizerState.Ready
    busy = SynthesizerState.Speaking
    paused = SynthesizerState.Paused


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
