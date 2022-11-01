# coding: utf-8

from __future__ import annotations
from io import StringIO
from bookworm import typehints as t
from bookworm.utils import escape_html
from bookworm.logger import logger
from .enumerations import SpeechElementKind, SsmlIdentifier


log = logger.getChild(__name__)

# A template for SSML content
SSML_TEMPLATE = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en"></speak>'




def _proc_text(content):
    return escape_html(content)


def _proc_ssml(content):
    return content


def _proc_sentence(content):
    return f'<s>{escape_html(content)}</s>'


def _proc_bookmark(content):
    return f'<mark name="{escape_html(content)}"/>'

def _proc_pause(content):
    pause_value = content
    if isinstance(pause_value, SsmlIdentifier):
        return f'<break strength="{pause_value.ssml_identifier}"/>'
    elif pause_value > 0:
        return f'<break time="{pause_value}ms"/>'
    return ""


def _proc_audio(content):
    return f'<audio src="{content}"/>'


SSML_PROC = {
    SpeechElementKind.text: _proc_text,
    SpeechElementKind.ssml: _proc_ssml,
    SpeechElementKind.sentence: _proc_sentence,
    SpeechElementKind.bookmark: _proc_bookmark,
    SpeechElementKind.pause: _proc_pause,
    SpeechElementKind.audio: _proc_audio,
}





def utterance_to_ssml(utterance, localeinfo: LocaleInfo):
    out = StringIO()
    for elem in utterance:
        kind, content = elem.kind, elem.content
        if (proc := SSML_PROC.get(kind)) is not None:
            text = proc(content)
        if kind is SpeechElementKind.start_paragraph:
            text = "<p>"
        elif kind is SpeechElementKind.start_voice:
            # Should we `escape_html` here?!
            text = f'<voice name="{content.name}">'
        elif kind is SpeechElementKind.start_emph:
            text = f'<emph level="{content}"'
        elif kind is SpeechElementKind.start_prosody:
            pitch, rate, volume = content
            text = "<prosody "
            if pitch:
                text += f'pitch="{pitch}" '
            if rate:
                if isinstance(rate, SsmlIdentifier):
                    text += f'rate="{rate.ssml_identifier}" '
                else:
                    text += f'rate="{rate}" '
            if volume:
                if isinstance(volume, SsmlIdentifier):
                    text += f'volume="{volume.ssml_identifier}" '
                else:
                    text += f'volume="{volume}" '
            text = text.strip() + ">"
        elif kind is SpeechElementKind.end_paragraph:
            text = "</p>"
        elif kind is SpeechElementKind.end_voice:
            text = "</voice>"
        elif kind is SpeechElementKind.end_emph:
            text = "</emph>"
        elif kind is SpeechElementKind.end_prosody:
            text = "</prosody>"
        out.write("\n" + text + "\n")
    if localeinfo is None:
        ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en">{out.getvalue()}</speak>'
    else:
        ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{localeinfo.ietf_tag}">{out.getvalue()}</speak>'
    return ssml
