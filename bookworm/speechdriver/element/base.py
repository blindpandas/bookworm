# coding: utf-8

from __future__ import annotations

import attr
from bookworm import typehints as t
from .enums import SpeechElementKind, EmphSpec, RateSpec, VolumeSpec


@attr.s(auto_attribs=True, hash=False)
class SpeechStyle:
    """Voice settings for a single utterance."""

    voice: VoiceInfo = None
    """VoiceInfo object."""

    emph: EmphSpec = None
    """Speech emphasis."""

    pitch: int = None
    """Speech pitch."""

    rate: t.Union[RateSpec, str] = None
    """Speech rate."""

    volume: t.Union[VolumeSpec, str] = None
    """Voice volume."""

    def __attrs_post_init__(self):
        self.__close_decompose = []

    def end_style_decompose(self):
        return self.__close_decompose

    def start_style_decompose(self):
        if self.voice:
            self.__close_decompose.append(SpeechElement(SpeechElementKind.end_voice, None))
            yield SpeechElement(SpeechElementKind.start_voice, self.voice)
        if self.emph:
            self.__close_decompose.append(SpeechElement(SpeechElementKind.end_emph, None))
            yield SpeechElement(SpeechElementKind.start_emph, self.emph)
        prosody_vals = (self.pitch, self.rate, self.volume)
        if any(prosody_vals):
            self.__close_decompose.append(SpeechElement(SpeechElementKind.end_prosody, prosody_vals))
            yield SpeechElement(SpeechElementKind.start_prosody, prosody_vals)


@attr.s(auto_attribs=True, slots=True, hash=False, frozen=True)
class SpeechElement:
    kind: SpeechElementKind
    content: t.Any
