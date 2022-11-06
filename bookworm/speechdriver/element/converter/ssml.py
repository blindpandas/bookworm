# coding: utf-8

from __future__ import annotations
from lxml import etree
from bookworm import typehints as t
from ..enums import SpeechElementKind, SsmlIdentifier
from .base import BaseSpeechConverter



class SsmlSpeechConverter(BaseSpeechConverter):
    __slots__ = []

    def start(self, localeinfo):
        lang_tag = localeinfo.ietf_tag if localeinfo else 'en'
        return f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang_tag}">'

    def end(self):
        return "</speak>"

    def text(self, content):
        return self.escape(content)

    def ssml(self, content):
        out = []
        for child in etree.fromstring(content):
            out.append(etree.tostring(child, encoding='unicode'))
        return "".join(out)

    def sentence(self, content):
        return f'<s>{self.escape(content)}</s>'

    def bookmark(self, content):
        return f'<mark name="{content}"/>'

    def pause(self, content):
        pause_value = content
        if isinstance(pause_value, SsmlIdentifier):
            return f'<break strength="{pause_value.ssml_identifier}"/>'
        elif pause_value > 0:
            return f'<break time="{pause_value}ms"/>'
        return ""

    def audio(self, content):
        return f'<audio src="{content}"/>'

    def start_paragraph(self, content):
        return "<p>"

    def end_paragraph(self, content):
        return "</p>"

    def start_voice(self, content):
        return f'<voice name="{content.name}">'

    def end_voice(self, content):
        return "</voice>"

    def start_emph(self, content):
        return f'<emph level="{content}">'

    def end_emph(self, content):
        return "</emph>"

    def start_prosody(self, content):
        text = ["<prosody "]
        pitch, rate, volume = content
        if pitch is not None:
            text.append(f' pitch="{pitch}" ')
        if rate is not None:
            if isinstance(rate, SsmlIdentifier):
                text.append(f' rate="{rate.ssml_identifier}" ')
            else:
                text.append(f' rate="{rate}" ')
        if volume is not None:
            if isinstance(volume, SsmlIdentifier):
                text.append(f' volume="{volume.ssml_identifier}" ')
            else:
                text.append(f' volume="{volume}" ')
        return "".join([*text, ">",])

    def end_prosody(self, content):
        return "</prosody>"



ssml_converter = SsmlSpeechConverter()
