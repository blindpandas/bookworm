# coding: utf-8

from __future__ import annotations

import codecs
from functools import lru_cache
from io import BytesIO, StringIO
from xml.sax.saxutils import escape

import attr
import chardet
import regex

from bookworm import typehints as t
from bookworm.logger import logger

try:
    from rapidfuzz.process import extract as fuzzy_matcher

    _IS_FUZZYWUZZY = False
except ImportError:
    from fuzzywuzzy.process import extractBests as fuzzy_matcher

    _IS_FUZZYWUZZY = True


log = logger.getChild(__name__)
FALLBACK_ENCODING = "latin1"


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


@attr.s(auto_attribs=True, slots=True, frozen=True, repr=False)
class TextContentDecoder:
    content: bytes
    prefered_encoding: str = "utf-8"
    fallback_encoding: str = FALLBACK_ENCODING

    def __repr__(self):
        return f"<{self.__class__.__name__}: content_length: {len(self.content)}, prefered_encoding: {self.prefered_encoding}>"

    def __len__(self) -> int:
        return len(self.content)
    
    @classmethod
    def from_filename(
        cls,
        filename: os.PathLike,
        prefered_encoding="utf-8",
        fallback_encoding=FALLBACK_ENCODING,
    ):
        with open(filename, "rb") as file:
            return cls(file.read(), prefered_encoding, fallback_encoding)

    def get_text(self):
        text, encoding = self.get_text_and_explain()
        return text

    def get_text_and_explain(self) -> tuple[str, str]:
        try:
            return self.content.decode(self.prefered_encoding), self.prefered_encoding
        except UnicodeDecodeError:
            pass
        encoding_res = chardet.detect(self.content[:5000])
        if encoding_res["confidence"] >= 0.5:
            try:
                return (
                    self.content.decode(encoding_res["encoding"], errors="replace"),
                    encoding_res["encoding"],
                )
            except UnicodeDecodeError:
                pass
        log.warning(
            f"Failed to detect content encoding. Resorting to '{FALLBACK_ENCODING}'"
        )
        return (
            self.content.decode(FALLBACK_ENCODING, errors="replace"),
            FALLBACK_ENCODING,
        )

    def get_utf8(self):
        __, encoding = self.get_text_and_explain()
        outbuf = BytesIO()
        encoded_file = codecs.EncodedFile(
            outbuf, data_encoding=encoding, file_encoding="utf-8", errors="replace"
        )
        encoded_file.write(self.content)
        return encoded_file.getvalue().decode("utf-8")


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
