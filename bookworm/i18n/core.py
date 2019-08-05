# coding: utf-8

import ctypes
import os
import gettext
import locale
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from System.Globalization import CultureInfo, CultureNotFoundException
from bookworm import app
from bookworm import paths
from bookworm import config
from bookworm.logger import logger
from .wx_i18n import set_wx_language


log = logger.getChild(__name__)

UNKNOWN_CULTURE_LCID = 4096
_AVAILABLE_LANGUAGES = None


class LanguageInfo:
    __slots__ = ["given_lang", "language", "culture"]

    def __init__(self, language):
        self.given_lang = language
        try:
            culture = CultureInfo.GetCultureInfoByIetfLanguageTag(language)
            self.culture = (
                culture if culture.LCID != UNKNOWN_CULTURE_LCID else culture.Parent
            )
            self.language = self.culture.IetfLanguageTag
        except CultureNotFoundException:
            raise ValueError(f"Invalid language {language}.")

    def __repr__(self):
        return f'LanguageInfo(language="{self.language}")'

    @property
    def LCID(self):
        return self.culture.LCID

    @property
    def pylang(self):
        return self.language.replace("-", "_")

    @property
    def description(self):
        return (
            self.culture.DisplayName,
            self.culture.NativeName,
            self.culture.EnglishName,
        )


def get_available_languages():
    """List the translations available from a directory"""
    global _AVAILABLE_LANGUAGES
    if _AVAILABLE_LANGUAGES:
        return _AVAILABLE_LANGUAGES
    folders = [item for item in Path(paths.locale_path()).iterdir() if item.is_dir()]
    langs = OrderedDict(en=LanguageInfo("en"))
    for entry in folders:
        try:
            if not entry.joinpath(f"LC_MESSAGES/{app.name}.mo").is_file():
                continue
            langinfo = LanguageInfo(entry.name)
            langs[langinfo.language] = langinfo
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
            set_wx_language(lang)
        CultureInfo.CurrentUICulture = langinfo.culture
        CultureInfo.DefaultThreadCurrentUICulture = langinfo.culture
        ctypes.windll.kernel32.SetThreadLocale(langinfo.LCID)
        app.current_language = langinfo
    except IOError:
        log.error(f"Translation catalog for language {lang} was not found.")
        app.current_language = get_available_languages()["default"]


def setup_i18n():
    set_active_language(config.conf["general"]["language"])


def is_rtl(lang):
    with suppress(ValueError):
        return CultureInfo(lang).TextInfo.IsRightToLeft
