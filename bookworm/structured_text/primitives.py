# coding: utf-8

"""Provides primitives for structuring a blob of text."""

from __future__ import annotations
import math
import bisect
import operator
import attr
from collections.abc import Container
from functools import cached_property
from more_itertools import locate
from bookworm import typehints as t
from bookworm.vendor.sentence_splitter import (
    SentenceSplitter,
    SentenceSplitterException,
    supported_languages as splitter_supported_languages,
)


@attr.s(auto_attribs=True, slots=True, hash=False)
class TextRange(Container):
    """Represents a text range refering to a substring."""

    start: int
    stop: int

    def __hash__(self):
        return hash((self.start, self.stop))

    @property
    def midrange(self):
        return math.floor((self.start + self.stop) / 2)

    def operator_imp(self, other, operator_func):
        if isinstance(other, self.__class__):
            return operator_func(self.start, other.start)
        elif type(other) is int:
            return operator_func(self.start, other)
        else:
            return NotImplemented

    def __gt__(self, other):
        return self.operator_imp(other, operator.gt)

    def __gte__(self, other):
        return self.operator_imp(other, operator.gte)

    def __lt__(self, other):
        return self.operator_imp(other, operator.lt)

    def __lte__(self, other):
        return self.operator_imp(other, operator.lte)

    def __contains__(self, pos):
        return self.start <= pos <= self.stop

    def __iter__(self):
        return iter((self.start, self.stop))

    def __hash__(self):
        return hash((self.start, self.stop))

    def astuple(self):
        return (self.start, self.stop)

    def as_slice(self):
        return slice(self.start, self.stop)


@attr.s(auto_attribs=True)
class TextInfo:
    """Provides basic structural information  about a blob of text
    Most of the properties have their values cached.
    """

    text: str
    """The text blob to process."""

    start_pos: int = 0
    """Starting position of the text, i.e. in a text control or a stream."""

    lang: str = "en"
    """The natural language of the text. Used in splitting the text into sentences."""

    eol: str = "\n"
    """The recognizable end-of-line sequence. Used to split the text into paragraphs."""

    sent_tokenizer: SentenceSplitter = None

    def __attrs_post_init__(self):
        lang = self.lang
        if lang not in splitter_supported_languages():
            lang = "en"
        if not self.text.endswith("\n"):
            self.text += "\n"
        self.sent_tokenizer = SentenceSplitter(lang)

    @cached_property
    def sentence_markers(self):
        return self._record_markers(self.sentences)

    @cached_property
    def paragraph_markers(self):
        return self._record_markers(self.paragraphs)

    def split_sentences(self, paragraph):
        return self.sent_tokenizer.split(paragraph)

    @cached_property
    def sentences(self):
        rv = []
        all_sents = set()
        for sent in self.split_sentences(self.text):
            all_sents.add(len(sent))
            if sent.strip():
                sent_start_pos = self.start_pos + sum(all_sents) + 1
                sent_range = TextRange(sent_start_pos, sent_start_pos + len(sent))
                rv.append((sent, sent_range))
        return rv

    @cached_property
    def paragraphs(self):
        rv = []
        paragraphs = self.text.splitlines(keepends=True)
        newline = "\n"
        p_locations = list(locate(self.text, lambda c: c == newline))
        start_locations = [0] + [l + 1 for l in p_locations[:-1]]
        for (start_pos, stop_pos), parag in zip(
            zip(start_locations, p_locations), paragraphs
        ):
            if not parag.strip():
                continue
            p_start_pos = self.start_pos + start_pos
            p_stop_pos = self.start_pos + stop_pos
            p_range = TextRange(start=p_start_pos, stop=p_stop_pos)
            rv.append((parag, p_range))
        return rv

    def _record_markers(self, segments):
        rv = []
        for _nope, pos in segments:
            rv.append(pos)
        return rv

    @cached_property
    def configured_markers(self):
        return self.paragraph_markers

    def get_paragraph_to_the_right_of(self, pos):
        marker_map = {item.start: item for item in self.configured_markers}
        markers = list(marker_map)
        markers.sort()
        index = bisect.bisect_right(markers, pos)
        if index < len(markers):
            return marker_map[markers[index]]
        elif index >= len(markers) and markers:
            return marker_map[markers[-1]]
        else:
            raise LookupError(
                f"Could not find a paragraph located at the right of position {pos}"
            )

    def get_paragraph_to_the_left_of(self, pos):
        marker_map = {item.start: item for item in self.configured_markers}
        markers = list(marker_map)
        markers.sort()
        if not markers:
            raise LookupError(
                f"Could not find a paragraph located at the left of position {pos}"
            )
        index = bisect.bisect_left(markers, pos)
        if index == 0:
            return marker_map[markers[0]]
        elif index > 0:
            return marker_map[markers[index - 1]]
        else:
            raise LookupError(
                f"Could not find a paragraph located at the left of position {pos}"
            )
