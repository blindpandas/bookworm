# coding: utf-8

"""Provides primitives for structuring a blob of text."""

import bisect
from collections.abc import Container
from functools import cached_property
from dataclasses import dataclass, field
from more_itertools import locate
from bookworm import typehints as t
from bookworm.vendor.sentence_splitter import (
    SentenceSplitter,
    SentenceSplitterException,
    supported_languages as splitter_supported_languages,
)


@dataclass(eq=True, order=True)
class TextRange(Container):
    """Represents a text range refering to a substring."""

    __slots__ = ["start", "stop"]

    start: int
    stop: int

    def __contains__(self, pos):
        return self.start <= pos <= self.stop

    def __iter__(self):
        return iter((self.start, self.stop))

    def __hash__(self):
        return hash((self.start, self.stop))

    def as_tuple(self):
        return (self.start, self.stop)

    def as_slice(self):
        return slice(self.start, self.stop)

@dataclass
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

    def __post_init__(self):
        lang = self.lang
        if lang not in splitter_supported_languages():
            lang = "en"
        self._sent_tokenizer = SentenceSplitter(lang)

    @cached_property
    def sentence_markers(self):
        return self._record_markers(self.sentences)

    @cached_property
    def paragraph_markers(self):
        return self._record_markers(self.paragraphs)

    def split_sentences(self, textblock):
        return self._sent_tokenizer.split(textblock)

    @cached_property
    def sentences(self):
        rv = []
        all_sents = set()
        for sent in self.split_sentences(self.text):
            all_sents.add(len(sent))
            if sent.strip():
                sent_start_pos = self.start_pos + sum(all_sents) + 1
                sent_range = TextRange(
                    sent_start_pos,
                    sent_start_pos + len(sent)
                )
                rv.append((sent, sent_range))
        return rv

    @cached_property
    def paragraphs(self):
        rv = []
        paragraphs = self.text.splitlines(keepends=True)
        newline = "\n"
        p_locations = list(locate(self.text, lambda c: c == newline))
        start_positions = [p + 1 for p in [-1,] + p_locations]
        end_positions = p_locations
        if p_locations and (p_locations[-1] != len(self.text)):
            end_positions += [len(self.text) - 1,] 
        for (start_pos, stop_pos, parag) in zip(start_positions, end_positions, paragraphs):
            if not parag.strip():
                continue
            p_start_pos = self.start_pos + start_pos
            p_range = TextRange(
                start=p_start_pos,
                stop=stop_pos
            )
            rv.append((parag,  p_range))
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
        markers = [trng.start for trng in self.configured_markers]
        markers.sort()
        index = bisect.bisect_right(markers, pos)
        if index < len(markers):
            return markers[index]
        elif index >= len(markers) and markers:
            return markers[-1]
        else:
            return pos

    def get_paragraph_to_the_left_of(self, pos):
        markers = [trng.start for trng in self.configured_markers]
        markers.sort()
        index = bisect.bisect_left(markers, pos)
        if index:
            return markers[index - 1]
        else:
            return 0
