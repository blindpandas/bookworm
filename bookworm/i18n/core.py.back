# coding: utf-8

import clr
from System.Globalization import CultureInfo, CultureNotFoundException

import ctypes
import os
import gettext
import locale
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from bookworm import app
from bookworm import paths
from bookworm import config
from bookworm.signals import app_started
from bookworm.logger import logger
from .wx_i18n import set_wx_language


log = logger.getChild(__name__)

UNKNOWN_CULTURE_LCID = 4096
_AVAILABLE_LANGUAGES = None


class LanguageInfo:
    __slots__ = ["given_lang", "language", "culture"]

    def __init__(self, given_lang):
        self.given_lang = given_lang
        try:
            culture = CultureInfo.GetCultureInfoByIetfLanguageTag(given_lang)
            self.culture = (
                culture if culture.LCID != UNKNOWN_CULTURE_LCID else culture.Parent
            )
            self.language = self.culture.IetfLanguageTag
        except CultureNotFoundException:
            raise ValueError(f"Invalid language {given_lang}.")

    def __repr__(self):
        return f'LanguageInfo(language="{self.language}")'

    def should_be_considered_equal_to(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f"{other} is not a LanguageInfo object.")
        if self.language.lower() == other.language.lower():
            return True
        this_root = self.language.split("-")[0].lower()
        other_root = other.language.split("-")[0].lower()
        if this_root == other_root:
            return True
        return False

    @property
    def LCID(self):
        return self.culture.LCID

    @property
    def pylang(self):
        return self.language.replace("-", "_")

    def get_display_info(self):
        return (
            self.culture.DisplayName,
            self.culture.NativeName,
            self.culture.EnglishName,
        )

    @property
    def description(self):
        info = self.get_display_info()
        desc = info[1]
        if info[1] != info[2]:
            desc = f"{info[2]} ({desc})"
        return desc


def get_available_languages(force_update=False):
    """List the translations available from a directory"""
    global _AVAILABLE_LANGUAGES
    if _AVAILABLE_LANGUAGES and not force_update:
        return _AVAILABLE_LANGUAGES
    folders = [item for item in Path(paths.locale_path()).iterdir() if item.is_dir()]
    langs = OrderedDict(en=LanguageInfo("en"))
    for entry in folders:
        try:
            if not entry.joinpath(f"LC_MESSAGES/{app.name}.mo").is_file():
                continue
            langinfo = LanguageInfo(entry.name)
            langs[langinfo.pylang] = langinfo
        except ValueError:
            continue
    current = None
    for lang in (CultureInfo.CurrentUICulture.Parent, CultureInfo.CurrentUICulture):
        if lang.IetfLanguageTag in langs:
            current = lang
    if current is not None:
        langs["default"] = langs[current.IetfLanguageTag]
    else:
        langs["default"] = langs["en"]
    _AVAILABLE_LANGUAGES = langs
    return langs


def set_active_language(language):
    log.debug(f"Setting display language to {language}.")
    langinfo = get_available_languages().get(language)
    if langinfo is None:
        langinfo = get_available_languages()["default"]
    lang = langinfo.pylang
    try:
        translation = gettext.translation(
            app.name, localedir=paths.locale_path(), languages=[language]
        )
        translation.install(names=["ngettext"])
        locale_changed = False
        with suppress(Exception):
            locale.setlocale(locale.LC_ALL, lang)
            locale_changed = True
        if not locale_changed:
            if "_" in lang:
                with suppress(Exception):
                    locale.setlocale(locale.LC_ALL, lang.split("_")[0])
                    locale_changed = True
        if not lang.startswith("en"):
            app_started.connect(lambda s: set_wx_language(lang), weak=False)
        CultureInfo.CurrentCulture = langinfo.culture
        CultureInfo.CurrentUICulture = langinfo.culture
        CultureInfo.DefaultThreadCurrentUICulture = langinfo.culture
        ctypes.windll.kernel32.SetThreadLocale(langinfo.LCID)
        app.current_language = langinfo
    except IOError:
        if lang != "en":
            log.error(f"Translation catalog for language {lang} was not found.")
        en_culture = CultureInfo.GetCultureInfoByIetfLanguageTag("en")
        CultureInfo.CurrentCulture = en_culture
        CultureInfo.CurrentUICulture = en_culture
        CultureInfo.DefaultThreadCurrentUICulture = en_culture
        ctypes.windll.kernel32.SetThreadLocale(en_culture.LCID)
        app.current_language = get_available_languages()["en"]


def setup_i18n():
    set_active_language(config.conf["general"]["language"])


def is_rtl(lang):
    with suppress(ValueError):
        return CultureInfo(lang).TextInfo.IsRightToLeft
