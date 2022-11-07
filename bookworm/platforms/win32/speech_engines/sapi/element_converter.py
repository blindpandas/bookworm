# coding: utf-8

from __future__ import annotations
from bookworm import typehints as t
from bookworm.speechdriver.element.converter.base import BaseSpeechConverter
from bookworm.speechdriver.element.enums import (
    SsmlIdentifier,
    PauseSpec,
    RateSpec,
    EmphSpec,
    VolumeSpec
)
from ..utils import create_audio_bookmark_name

PAUSE_MAP = {
    PauseSpec.null: 0,
    PauseSpec.extra_small: 50,
    PauseSpec.small: 150,
    PauseSpec.medium: 300,
    PauseSpec.large: 500,
    PauseSpec.extra_large: 1000
}
RATE_MAP = {
    RateSpec.extra_slow: 20,
    RateSpec.slow: 30,
    RateSpec.medium: 50,
    RateSpec.fast: 70,
    RateSpec.extra_fast: 90,
}
VOLUME_SPEC = {
    VolumeSpec.default: 75,
    VolumeSpec.silent: 0,
    VolumeSpec.extra_soft: 20,
    VolumeSpec.soft: 40,
    VolumeSpec.medium: 50,
    VolumeSpec.loud: 80,
    VolumeSpec.extra_loud: 100,
}


class SapiSpeechConverter(BaseSpeechConverter):
    __slots__ = []

    def start(self, localeinfo):
        return '<xml version="1.0">'

    def end(self):
        return '</xml>'

    def text(self, content):
        return self.escape(content)

    def ssml(self, content):
        return ""
        raise NotImplementedError

    def sentence(self, content):
        return self.text(content)

    def bookmark(self, content):
        return f'<bookmark mark="{self.escape(content)}"/>'

    def pause(self, content):
        pause_value = content if not isinstance(content, SsmlIdentifier) else PAUSE_MAP[content] 
        return f'<silence msec="{pause_value}"/>'

    def audio(self, content):
        return self.bookmark(create_audio_bookmark_name(content))

    def start_paragraph(self, content):
        return "\r\n"

    def end_paragraph(self, content):
        return "\r\n"

    def start_voice(self, content):
        return f'<voice required="Name={content.name}">'

    def end_voice(self, content):
        return "</voice>"

    def start_emph(self, content):
        if isinstance(content, SsmlIdentifier) and content is EmphSpec.not_set:
            return
        return f'<emph>'

    def end_emph(self, content):
        return "</emph>"

    def start_prosody(self, content):
        pitch, rate, volume = content
        text = []
        if pitch is not None:
            pitchvalue = self._percentToPitch(pitch)
            text.append(f'<pitch absmiddle="{pitchvalue}">')
        if rate not in (None, RateSpec.not_set):
            ratevalue = rate if not isinstance(rate, SsmlIdentifier) else RATE_MAP[rate]
            text.append(f'<rate absspeed="{self._percentToRate(ratevalue)}">')
        if volume not in (None, VolumeSpec.not_set):
            volumevalue = volume if not isinstance(volume, SsmlIdentifier) else VOLUME_MAP[volume]
            text.append(f'<volume level="{volumevalue}">')
        return "".join(text)

    def end_prosody(self, content):
        pitch, rate, volume = content
        text = []
        if pitch is not None:
            text.append("</pitch>")
        if rate is not None:
            text.append("</rate>")
        if volume is not None:
            text.append("</volume>")
        return "".join(text)

    def _percentToRate(self, percent):
        return (percent - 50) // 5

    def _percentToPitch(self, percent):
        return percent // 2 - 25



sapi_speech_converter = SapiSpeechConverter()
