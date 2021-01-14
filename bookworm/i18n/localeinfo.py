# coding: utf-8

import locale
from babel import UnknownLocaleError, Locale, parse_locale, default_locale


class LocaleInfo:
    __slots__ = ["identifier", "language", "locale"]

    def __init__(self, identifier):
        self.identifier = identifier.replace(" ", "_").replace("-", "_")
        try:
            self.locale = Locale.parse(self.identifier)
            self.language = self.locale.language
        except UnknownLocaleError:
            raise ValueError(f"Invalid locale identifier {identifier}.")

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
