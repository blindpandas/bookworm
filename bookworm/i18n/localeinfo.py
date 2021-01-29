# coding: utf-8

import locale
from babel import UnknownLocaleError, Locale, parse_locale, default_locale
from languagecodes import iso_639_alpha2
from languagecodes.synonyms import expand_synonyms

class LocaleInfo:
    __slots__ = ["identifier", "original_code", "language", "locale"]

    def __init__(self, identifier, *, original_code=None):
        self.original_code = original_code if original_code is not None else identifier
        self.identifier = identifier.replace(" ", "_").replace("-", "_")
        try:
            self.locale = Locale.parse(self.identifier)
            self.language = self.locale.language
        except UnknownLocaleError:
            raise ValueError(f"Invalid locale identifier {identifier}.")

    @classmethod
    def from_babel_locale(cls, babel_locale, *args, **kwargs):
        return cls(str(babel_locale), *args, **kwargs)

    @classmethod
    def from_three_letter_code(cls, lang_code, *args, **kwargs):
        try:
            return cls.from_babel_locale(Locale.parse(lang_code), original_code=lang_code)
        except (ValueError, UnknownLocaleError):
            lang = iso_639_alpha2(lang_code)
            if lang is None:
                lang = iso_639_alpha2(lang_code.split("_")[0])
            if lang is not None:
                return cls(lang, original_code=lang_code)
        raise ValueError(f"Invalid 3-letter language code {lang_code}.")

    def __repr__(self):
        return f'LocaleInfo(identifier="{self.identifier}");language={self.language}'

    def __eq__(self, other):
        if not getattr(other, "locale"):
            return NotImplemented
        return self.locale == other.locale

    def __hash__(self):
        return hash(self.locale)

    def should_be_considered_equal_to(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f"{other} is not a LocaleInfo object.")
        if self.language.lower() == other.language.lower():
            return True
        return False

    @property
    def parent(self):
        return LocaleInfo(self.language)

    @property
    def pylang(self):
        return str(self.locale)

    @property
    def ietf_tag(self):
        return "-".join((self.language, self.locale.territory))

    def get_display_info(self):
        return (
            self.locale.english_name,
            self.locale.display_name,
            self.locale.english_name,
        )

    @property
    def description(self):
        info = self.get_display_info()
        desc = info[1]
        if info[1] != info[2]:
            desc = f"{info[2]} ({desc})"
        return desc
