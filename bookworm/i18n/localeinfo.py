# coding: utf-8

from __future__ import annotations

import locale

import babel.numbers
from babel import Locale, UnknownLocaleError, default_locale, parse_locale
from babel.dates import format_date as babel_format_date
from babel.dates import format_datetime as babel_format_datetime
from languagecodes import iso_639_alpha2
from tzlocal import get_localzone


class LocaleInfo:
    __slots__ = ["identifier", "given_locale_name", "language", "locale"]

    def __init__(self, identifier, *, given_locale_name=None):
        self.identifier = identifier.replace(" ", "_").replace("-", "_")
        self.given_locale_name = (
            given_locale_name if given_locale_name is not None else identifier
        )
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
            return cls.from_babel_locale(
                Locale.parse(lang_code), given_locale_name=lang_code
            )
        except (ValueError, UnknownLocaleError):
            lang = iso_639_alpha2(lang_code)
            if lang is None:
                lang = iso_639_alpha2(lang_code.split("_")[0])
            if lang is not None:
                return cls(lang, given_locale_name=lang_code)
        raise ValueError(f"Invalid 3-letter language code {lang_code}.")

    def __repr__(self):
        return f'LocaleInfo(identifier="{self.identifier}");language={self.language}'

    def __eq__(self, other):
        if not getattr(other, "locale", None):
            return NotImplemented
        return self.locale == other.locale

    def __hash__(self):
        return hash(self.locale)

    def __getstate__(self) -> dict:
        """Support for pickling."""
        return dict(
            identifier=self.identifier, given_locale_name=self.given_locale_name
        )

    def __setstate__(self, state):
        """Support for unpickling."""
        self.__init__(**state)

    def should_be_considered_equal_to(self, other, strict=False):
        if not isinstance(other, LocaleInfo):
            raise TypeError(f"{other} is not a LocaleInfo object.")
        if strict:
            return self == other
        return self.two_letter_language_code == other.two_letter_language_code

    @property
    def two_letter_language_code(self):
        return self.locale.language

    @property
    def parent(self):
        return LocaleInfo(self.two_letter_language_code)

    @property
    def pylang(self):
        return self.ietf_tag.replace("-", "_")

    @property
    def ietf_tag(self):
        if self.locale.territory is None:
            return self.language
        return "-".join([self.language, self.locale.territory.upper()])

    @property
    def is_rtl(self):
        return self.locale.text_direction.lower() == "rtl"

    @property
    def english_name(self):
        return self.locale.english_name

    @property
    def localized_name(self):
        return self.locale.display_name

    def get_display_info(self):
        return (
            self.locale.english_name,
            self.locale.display_name,
            self.locale.english_name,
        )

    @property
    def native_name(self):
        return self.locale.display_name

    @property
    def description(self):
        info = self.get_display_info()
        desc = info[1]
        if info[1] != info[2]:
            desc = f"{info[2]} ({desc})"
        return desc

    def format_datetime(self, datetime_obj, date_only, format, localized) -> str:
        if date_only:
            return babel_format_date(datetime_obj, format=format, locale=self.locale)
        else:
            if localized:
                tzinfo = get_localzone()
            else:
                tzinfo = None
            return babel_format_datetime(
                datetime_obj, format=format, tzinfo=tzinfo, locale=self.locale
            )

    def format_percentage(self, percentage):
        return babel.numbers.format_percent(percentage, locale=self.locale)
