
"""Provides primitives for structuring a blob of text."""

from __future__ import annotations

import bisect
import math
import operator
from collections.abc import Container
from functools import cached_property, partial

import attr
from more_itertools import locate
from pytqsm import segment as segment_sentences

from bookworm import typehints as t

TEXT_OBJECT_REPLACEMENT_CHAR = "\ufffc"
CURRENT_POSITION_MODEL_VERSION = 2
CURRENT_CONTENT_HASH_VERSION = 2


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
        if type(other) is int:
            return operator_func(self.start, other)
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


@attr.s(auto_attribs=True, slots=True, frozen=True)
class TextPositionReplacement:
    display_start: int
    display_stop: int
    storage_start: int
    storage_stop: int

    @property
    def display_length(self):
        return self.display_stop - self.display_start

    @property
    def storage_length(self):
        return self.storage_stop - self.storage_start


@attr.s(auto_attribs=True, slots=True, frozen=True)
class TextPositionMap:
    """Maps user-visible text offsets to stable storage offsets."""

    display_length: int
    storage_length: int
    replacements: tuple[TextPositionReplacement, ...] = ()

    @classmethod
    def identity(cls, text_length=0):
        return cls(
            display_length=max(text_length, 0),
            storage_length=max(text_length, 0),
        )

    @classmethod
    def from_collapsed_ranges(cls, display_text, ranges, replacement_text=None):
        replacement_text = replacement_text or TEXT_OBJECT_REPLACEMENT_CHAR
        normalized_ranges = []
        previous_stop = 0
        for text_range in sorted(ranges, key=lambda rng: (rng.start, rng.stop)):
            start = max(0, text_range.start)
            stop = min(len(display_text), text_range.stop)
            if stop <= start or start < previous_stop:
                continue
            normalized_ranges.append(TextRange(start, stop))
            previous_stop = stop
        if not normalized_ranges:
            return display_text, cls.identity(len(display_text))

        storage_chunks = []
        replacements = []
        display_cursor = 0
        storage_cursor = 0
        for display_range in normalized_ranges:
            prefix = display_text[display_cursor : display_range.start]
            storage_chunks.append(prefix)
            storage_cursor += len(prefix)
            storage_start = storage_cursor
            storage_chunks.append(replacement_text)
            storage_cursor += len(replacement_text)
            replacements.append(
                TextPositionReplacement(
                    display_start=display_range.start,
                    display_stop=display_range.stop,
                    storage_start=storage_start,
                    storage_stop=storage_cursor,
                )
            )
            display_cursor = display_range.stop
        suffix = display_text[display_cursor:]
        storage_chunks.append(suffix)
        storage_cursor += len(suffix)
        return "".join(storage_chunks), cls(
            display_length=len(display_text),
            storage_length=storage_cursor,
            replacements=tuple(replacements),
        )

    @classmethod
    def from_texts(cls, display_text, storage_text):
        """Build a position map between two mostly-identical text models."""
        if display_text == storage_text:
            return cls.identity(len(display_text))
        display_length = len(display_text)
        storage_length = len(storage_text)
        replacements = []
        display_cursor = 0
        storage_cursor = 0
        while display_cursor < display_length and storage_cursor < storage_length:
            if display_text[display_cursor] == storage_text[storage_cursor]:
                display_cursor += 1
                storage_cursor += 1
                continue
            display_anchor, storage_anchor = cls._find_alignment_anchor(
                display_text,
                storage_text,
                display_cursor,
                storage_cursor,
            )
            replacements.append(
                TextPositionReplacement(
                    display_start=display_cursor,
                    display_stop=display_anchor,
                    storage_start=storage_cursor,
                    storage_stop=storage_anchor,
                )
            )
            display_cursor = display_anchor
            storage_cursor = storage_anchor
        if display_cursor < display_length or storage_cursor < storage_length:
            replacements.append(
                TextPositionReplacement(
                    display_start=display_cursor,
                    display_stop=display_length,
                    storage_start=storage_cursor,
                    storage_stop=storage_length,
                )
            )
        return cls(
            display_length=display_length,
            storage_length=storage_length,
            replacements=tuple(replacements),
        )

    @staticmethod
    def _find_alignment_anchor(display_text, storage_text, display_start, storage_start):
        anchor_lengths = (48, 32, 24, 16, 12, 8, 6, 4, 3, 2, 1)
        search_window = 4096
        display_length = len(display_text)
        storage_length = len(storage_text)
        best = None
        for anchor_length in anchor_lengths:
            if display_start + anchor_length <= display_length:
                display_offset_limit = min(
                    search_window,
                    display_length - display_start - anchor_length,
                )
                storage_limit = min(
                    storage_length,
                    storage_start + search_window + anchor_length,
                )
                for display_offset in range(display_offset_limit + 1):
                    if best is not None and display_offset > best[0]:
                        break
                    anchor_start = display_start + display_offset
                    anchor = display_text[anchor_start : anchor_start + anchor_length]
                    storage_anchor = storage_text.find(anchor, storage_start, storage_limit)
                    if storage_anchor != -1:
                        score = display_offset + (storage_anchor - storage_start)
                        candidate = (score, -anchor_length, anchor_start, storage_anchor)
                        if best is None or candidate < best:
                            best = candidate
            if storage_start + anchor_length <= storage_length:
                storage_offset_limit = min(
                    search_window,
                    storage_length - storage_start - anchor_length,
                )
                display_limit = min(
                    display_length,
                    display_start + search_window + anchor_length,
                )
                for storage_offset in range(storage_offset_limit + 1):
                    if best is not None and storage_offset > best[0]:
                        break
                    anchor_start = storage_start + storage_offset
                    anchor = storage_text[anchor_start : anchor_start + anchor_length]
                    display_anchor = display_text.find(anchor, display_start, display_limit)
                    if display_anchor != -1:
                        score = storage_offset + (display_anchor - display_start)
                        candidate = (score, -anchor_length, display_anchor, anchor_start)
                        if best is None or candidate < best:
                            best = candidate
        if best is not None:
            return best[2], best[3]
        return display_length, storage_length

    @staticmethod
    def _clamp(pos):
        return max(pos, 0)

    def display_to_storage_position(self, pos, affinity="before"):
        pos = self._clamp(pos)
        delta = 0
        for replacement in self.replacements:
            if pos < replacement.display_start:
                break
            if (
                replacement.display_length == 0
                and pos == replacement.display_start
            ):
                return (
                    replacement.storage_stop if affinity == "after" else replacement.storage_start
                )
            if replacement.display_start <= pos < replacement.display_stop:
                return (
                    replacement.storage_stop if affinity == "after" else replacement.storage_start
                )
            delta += replacement.display_length - replacement.storage_length
        return self._clamp(pos - delta)

    def storage_to_display_position(self, pos, affinity="before"):
        pos = self._clamp(pos)
        delta = 0
        for replacement in self.replacements:
            if pos < replacement.storage_start:
                break
            if (
                replacement.storage_length == 0
                and pos == replacement.storage_start
            ):
                return (
                    replacement.display_stop if affinity == "after" else replacement.display_start
                )
            if replacement.storage_start <= pos < replacement.storage_stop:
                return (
                    replacement.display_stop if affinity == "after" else replacement.display_start
                )
            delta += replacement.display_length - replacement.storage_length
        return self._clamp(pos + delta)

    def _display_to_storage_range_stop(self, pos):
        pos = self._clamp(pos)
        delta = 0
        for replacement in self.replacements:
            if pos < replacement.display_start:
                break
            if pos == replacement.display_start:
                return self._clamp(pos - delta)
            if replacement.display_start < pos < replacement.display_stop:
                return replacement.storage_stop
            delta += replacement.display_length - replacement.storage_length
        return self._clamp(pos - delta)

    def _storage_to_display_range_stop(self, pos):
        pos = self._clamp(pos)
        delta = 0
        for replacement in self.replacements:
            if pos < replacement.storage_start:
                break
            if pos == replacement.storage_start:
                return self._clamp(pos + delta)
            if replacement.storage_start < pos < replacement.storage_stop:
                return replacement.display_stop
            delta += replacement.display_length - replacement.storage_length
        return self._clamp(pos + delta)

    def display_to_storage_range(self, start, stop):
        start_affinity = "before"
        if start < stop:
            for replacement in self.replacements:
                if start < replacement.display_start:
                    break
                if (
                    replacement.display_length == 0
                    and start == replacement.display_start
                ):
                    start_affinity = "after"
                    break
        storage_start = self.display_to_storage_position(start, affinity=start_affinity)
        storage_stop = self._display_to_storage_range_stop(stop)
        return TextRange(storage_start, max(storage_start, storage_stop))

    def storage_to_display_range(self, start, stop):
        display_start = self.storage_to_display_position(start, affinity="before")
        display_stop = self._storage_to_display_range_stop(stop)
        return TextRange(display_start, max(display_start, display_stop))


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

    sent_tokenizer: t.Any = None

    def __attrs_post_init__(self):
        if not self.text.endswith("\n"):
            self.text += "\n"
        self.sent_tokenizer = partial(segment_sentences, self.lang)

    @cached_property
    def sentence_markers(self):
        return self._record_markers(self.sentences)

    @cached_property
    def paragraph_markers(self):
        return self._record_markers(self.paragraphs)

    def split_sentences(self, paragraph):
        return self.sent_tokenizer(paragraph)

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
        for (start_pos, stop_pos), parag in zip(zip(start_locations, p_locations), paragraphs):
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
        if index >= len(markers) and markers:
            return marker_map[markers[-1]]
        raise LookupError(f"Could not find a paragraph located at the right of position {pos}")

    def get_paragraph_to_the_left_of(self, pos):
        marker_map = {item.start: item for item in self.configured_markers}
        markers = list(marker_map)
        markers.sort()
        if not markers:
            raise LookupError(f"Could not find a paragraph located at the left of position {pos}")
        index = bisect.bisect_left(markers, pos)
        if index == 0:
            return marker_map[markers[0]]
        if index > 0:
            return marker_map[markers[index - 1]]
        raise LookupError(f"Could not find a paragraph located at the left of position {pos}")
