import os
import warnings
from enum import Enum
from pathlib import Path
from typing import List

import regex

from bookworm.paths import app_path

__all__ = (
    "SentenceSplitter",
    "split_text_into_sentences",
    "SentenceSplitterException",
    "SentenceSplitterWarning",
    "supported_languages",
)


class SentenceSplitterException(Exception):
    """Sentence splitter exception."""

    pass


class SentenceSplitterWarning(Warning):
    """Sentence splitter warning."""

    pass


_supported_lans = []


def supported_languages():
    global _supported_lans
    if not _supported_lans:
        nbp_path = app_path("resources", "non_breaking_prefixes")
        _supported_lans = [file[:-4] for file in os.listdir(nbp_path)]
    return _supported_lans


class SentenceSplitter(object):
    """Text to sentence splitter using heuristic algorithm by Philipp Koehn and Josh Schroeder.."""

    class PrefixType(Enum):
        DEFAULT = 1
        NUMERIC_ONLY = 2

    __slots__ = [
        # Dictionary of non-breaking prefixes; keys are string prefixes, values are PrefixType enums
        "__non_breaking_prefixes"
    ]

    def __init__(self, language: str, non_breaking_prefix_file: str = None):
        """Create sentence splitter object.

        :param language: ISO 639-1 language code
        :param non_breaking_prefix_file: path to non-breaking prefix file
        """
        if not regex.match(
            pattern=r"^[a-z][a-z]$", string=language, flags=regex.UNICODE
        ):
            raise SentenceSplitterException(
                "Invalid language code: {}".format(language)
            )

        if non_breaking_prefix_file is None:
            non_breaking_prefix_file = app_path(
                "resources", "non_breaking_prefixes", f"{language}.txt"
            )

        if not Path(non_breaking_prefix_file).exists():
            raise SentenceSplitterException(
                "Non-breaking prefix file for language '{}' was not found at path '{}'".format(
                    language, non_breaking_prefix_file
                )
            )

        self.__non_breaking_prefixes = dict()
        with open(non_breaking_prefix_file, mode="r", encoding="utf-8") as prefix_file:
            for line in prefix_file.readlines():
                if "#NUMERIC_ONLY#" in line:
                    prefix_type = SentenceSplitter.PrefixType.NUMERIC_ONLY
                else:
                    prefix_type = SentenceSplitter.PrefixType.DEFAULT

                # Remove comments
                line = regex.sub(
                    pattern=r"#.*",
                    repl="",
                    string=line,
                    flags=regex.DOTALL | regex.UNICODE,
                )

                line = line.strip()

                if not line:
                    continue

                self.__non_breaking_prefixes[line] = prefix_type

    def split(self, text: str) -> List[str]:
        """Split text into sentences.

        :param text: Text to be split into individual sentences
        :return: List of string sentences
        """
        if text is None:
            warnings.warn("Text is None.", SentenceSplitterWarning)
            return []

        if not text:
            return []

        # Add sentence breaks as needed:

        # Non-period end of sentence markers (?!) followed by sentence starters
        text = regex.sub(
            pattern=r'([?!]) +([\'"([\u00bf\u00A1\p{Initial_Punctuation}]*[\p{Uppercase_Letter}\p{Other_Letter}])',
            repl="\\1\n\\2",
            string=text,
            flags=regex.UNICODE,
        )

        # Multi-dots followed by sentence starters
        text = regex.sub(
            pattern=r'(\.[\.]+) +([\'"([\u00bf\u00A1\p{Initial_Punctuation}]*[\p{Uppercase_Letter}\p{Other_Letter}])',
            repl="\\1\n\\2",
            string=text,
            flags=regex.UNICODE,
        )

        # Add breaks for sentences that end with some sort of punctuation inside a quote or parenthetical and are
        # followed by a possible sentence starter punctuation and upper case
        text = regex.sub(
            pattern=(
                r'([?!\.][\ ]*[\'")\]\p{Final_Punctuation}]+) +([\'"([\u00bf\u00A1\p{Initial_Punctuation}]*[\ ]*'
                r"[\p{Uppercase_Letter}\p{Other_Letter}])"
            ),
            repl="\\1\n\\2",
            string=text,
            flags=regex.UNICODE,
        )
        # Add breaks for sentences that end with some sort of punctuation are followed by a sentence starter punctuation
        # and upper case
        text = regex.sub(
            pattern=(
                r'([?!\.]) +([\'"[\u00bf\u00A1\p{Initial_Punctuation}]+[\ ]*[\p{Uppercase_Letter}\p{Other_Letter}])'
            ),
            repl="\\1\n\\2",
            string=text,
            flags=regex.UNICODE,
        )

        # Special punctuation cases are covered. Check all remaining periods
        words = regex.split(pattern=r" +", string=text, flags=regex.UNICODE)
        text = ""
        for i in range(0, len(words) - 1):
            match = regex.search(
                pattern=r"([\w\.\-]*)([\'\"\)\]\%\p{Final_Punctuation}]*)(\.+)$",
                string=words[i],
                flags=regex.UNICODE,
            )
            if match:
                prefix = match.group(1)
                starting_punct = match.group(2)

                def is_prefix_honorific(prefix_: str, starting_punct_: str) -> bool:
                    """Check if \\1 is a known honorific and \\2 is empty."""
                    if prefix_:
                        if prefix_ in self.__non_breaking_prefixes:
                            if (
                                self.__non_breaking_prefixes[prefix_]
                                == SentenceSplitter.PrefixType.DEFAULT
                            ):
                                if not starting_punct_:
                                    return True
                    return False

                if is_prefix_honorific(prefix_=prefix, starting_punct_=starting_punct):
                    # Not breaking
                    pass

                elif regex.search(
                    pattern=r"(\.)[\p{Uppercase_Letter}\p{Other_Letter}\-]+(\.+)$",
                    string=words[i],
                    flags=regex.UNICODE,
                ):
                    # Not breaking - upper case acronym
                    pass

                elif regex.search(
                    pattern=(
                        r'^([ ]*[\'"([\u00bf\u00A1\p{Initial_Punctuation}]*[ ]*[\p{Uppercase_Letter}'
                        r"\p{Other_Letter}0-9])"
                    ),
                    string=words[i + 1],
                    flags=regex.UNICODE,
                ):

                    def is_numeric(prefix_: str, starting_punct_: str, next_word: str):
                        """The next word has a bunch of initial quotes, maybe a space, then either upper case or a
                        number."""
                        if prefix_:
                            if prefix_ in self.__non_breaking_prefixes:
                                if (
                                    self.__non_breaking_prefixes[prefix_]
                                    == SentenceSplitter.PrefixType.NUMERIC_ONLY
                                ):
                                    if not starting_punct_:
                                        if regex.search(
                                            pattern="^[0-9]+",
                                            string=next_word,
                                            flags=regex.UNICODE,
                                        ):
                                            return True
                        return False

                    if not is_numeric(
                        prefix_=prefix,
                        starting_punct_=starting_punct,
                        next_word=words[i + 1],
                    ):
                        words[i] = words[i] + "\n"

                    # We always add a return for these unless we have a numeric non-breaker and a number start

            text = text + words[i] + " "

        # We stopped one token from the end to allow for easy look-ahead. Append it now.
        text = text + words[-1]

        # Clean up spaces at head and tail of each line as well as any double-spacing
        text = regex.sub(pattern=" +", repl=" ", string=text)
        text = regex.sub(pattern="\n ", repl="\n", string=text)
        text = regex.sub(pattern=" \n", repl="\n", string=text)
        text = text.strip()

        sentences = text.split("\n")

        return sentences


def split_text_into_sentences(
    text: str, language: str, non_breaking_prefix_file: str = None
) -> List[str]:
    """Split text into sentences.

    For better performance, use SentenceSplitter class directly to avoid reloading non-breaking prefix file on every
    call.

    :param text: Text to be split into individual sentences
    :param language: ISO 639-1 language code
    :param non_breaking_prefix_file: path to non-breaking prefix file
    :return: List of string sentences
    """
    splitter = SentenceSplitter(
        language=language, non_breaking_prefix_file=non_breaking_prefix_file
    )
    return splitter.split(text=text)
