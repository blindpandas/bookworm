# coding: utf-8

from __future__ import annotations
import regex
from functools import lru_cache
from xml.sax.saxutils import escape
from bookworm import typehints as t
from bookworm.logger import logger


try:
    from rapidfuzz.process import extract as fuzzy_matcher

    _IS_FUZZYWUZZY = False
except ImportError:
    from fuzzywuzzy.process import extractBests as fuzzy_matcher

    _IS_FUZZYWUZZY = True


log = logger.getChild(__name__)


_T = t.TypeVar("T")


# Taken from: https://stackoverflow.com/a/47248784
URL_REGEX = regex.compile(
    r"""(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))"""
)
URL_BAD_CHARS = "'\\.,[](){}:;\""


# New line character
UNIX_NEWLINE = "\n"
WINDOWS_NEWLINE = "\r\n"
MAC_NEWLINE = "\r"
NEWLINE = UNIX_NEWLINE
MORE_THAN_ONE_LINE = regex.compile(r"[\n]{2,}")
EXCESS_LINE_REPLACEMENT_FUNC = lambda m: m[0].replace("\n", " ")[:-1] + "\n"


def normalize_line_breaks(text, line_break=UNIX_NEWLINE):
    return text.replace("\r", " ")


def remove_excess_blank_lines(text):
    return MORE_THAN_ONE_LINE.sub(
        EXCESS_LINE_REPLACEMENT_FUNC, normalize_line_breaks(text)
    )


def fuzzy_search(
    query: str,
    choices: list[_T],
    limit: int = 25,
    score_cutoff: float = 50,
    string_converter=str,
) -> list[_T]:
    if _IS_FUZZYWUZZY:
        match_choices = {
            idx: string_converter(item) for (idx, item) in enumerate(choices)
        }
    else:
        match_choices = [string_converter(c) for c in choices]
    return [
        choices[idx]
        for (__, __, idx) in fuzzy_matcher(
            query, match_choices, limit=limit, score_cutoff=score_cutoff
        )
    ]


@lru_cache(maxsize=5)
def get_url_spans(text):
    return tuple(
        (span := m.span(), text[slice(*span)].strip(URL_BAD_CHARS))
        for m in URL_REGEX.finditer(text)
    )


def is_external_url(text):
    return URL_REGEX.match(text) is not None


def escape_html(text):
    """Escape the text so as to be used
    as a part of an HTML document.

    Taken from python Wiki.
    """
    html_escape_table = {'"': "&quot;", "'": "&apos;"}
    return escape(text, html_escape_table)
