# coding: utf-8

"""
Contains generic utility functions for working with documents.
The functions in this module are usually run in parallel using bookworm.concurrency .QueueProcess.
"""

from __future__ import annotations

from io import StringIO

import attr
import regex as re

from bookworm.structured_text import TextRange

NEWLINE = "\n"


@attr.s(auto_attribs=True, slots=True, getstate_setstate=True)
class SearchRequest:
    """
    Contains info about a search operation.
    """

    term: str
    is_regex: bool
    case_sensitive: bool
    whole_word: bool
    from_page: int = None
    to_page: int = None
    text_range: TextRange = None
    text: str = None


@attr.s(auto_attribs=True, slots=True, getstate_setstate=True)
class SearchResult:
    """Holds information about a single search result."""

    excerpt: str
    page: int
    position: int
    section: str
    match_range: TextRange = None

    def __attrs_post_init__(self):
        if self.match_range is None:
            self.match_range = TextRange(self.position, self.position)


def search(pattern, text):
    """Search the given text using a regular expression."""
    snip_reach = 25
    len_text = len(text)
    for mat in pattern.finditer(text, concurrent=True):
        start, end = mat.span()
        snip_start = 0 if start <= snip_reach else (start - snip_reach)
        snip_end = len_text if (end + snip_reach) >= len_text else (end + snip_reach)
        snip = text[snip_start:snip_end].split()
        if len(snip) > 3:
            snip.pop(0)
            snip.pop(-1)
        yield (TextRange(start, end), " ".join(snip))


def export_to_plain_text(doc, target_filename):
    """This function runs in a separate process."""
    total = len(doc)
    out = StringIO()
    if out.write(doc.metadata.title or ""):
        out.write(f"{NEWLINE}{'-' * 30}{NEWLINE}")
    try:
        for n in range(total):
            text = doc.get_page_content(n)
            out.write(f"{text}{NEWLINE}\f{NEWLINE}")
            yield n + 1
        full_text = out.getvalue()
        with open(target_filename, "w", encoding="utf8") as file:
            file.write(full_text)
    finally:
        out.close()
        doc.close()


def search_book(doc, request):
    """This function also runs in a separate process."""
    pattern = _make_search_re_pattern(request)
    try:
        for n in range(request.from_page, request.to_page + 1):
            resultset = []
            sect = doc[n].section.title
            for match_range, snip in search(pattern, doc.get_page_content(n)):
                resultset.append(
                    SearchResult(
                        excerpt=snip,
                        page=n,
                        position=match_range.start,
                        section=sect,
                        match_range=match_range,
                    )
                )
            yield resultset
    finally:
        doc.close()


def search_single_page_document(text, request):
    pattern = _make_search_re_pattern(request)
    start_pos = request.text_range.start
    for match_range, snip in search(pattern, text):
        actual_match_range = TextRange(
            start_pos + match_range.start,
            start_pos + match_range.stop,
        )
        yield [
            SearchResult(
                excerpt=snip,
                page=0,
                position=actual_match_range.start,
                section="",
                match_range=actual_match_range,
            ),
        ]


def _make_search_re_pattern(request):
    I = re.I if not request.case_sensitive else 0
    if request.is_regex:
        term = request.term
        term = rf"({term})"
    else:
        term = re.escape(request.term, literal_spaces=True)
        term = rf"({term})"
        if request.whole_word:
            term = rf"\b{term}\b"
    return re.compile(term, I | re.M)
