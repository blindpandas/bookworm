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
from bookworm.logger import logger


log = logger.getChild(__name__)
UNKNOWN_CULTURE_LCID = 4096


class LanguageInfo:
    __slots__ = ["language", "culture"]

    def __init__(self, language):
        try:
            culture = CultureInfo.GetCultureInfoByIetfLanguageTag(language)
            self.culture = culture if culture.LCID != UNKNOWN_CULTURE_LCID else culture.Parent
            self.language = self.culture.IetfLanguageTag
        except CultureNotFoundException:
            raise ValueError(f"Invalid language {language}.")

    def __repr__(self):
        return f'LanguageInfo(language="{self.language}")'

    @property
    def LCID(self):
        return self.culture.LCID

    @property
    def description(self):
        return self.culture.DisplayName, self.culture.NativeName


def get_available_languages():
    """List the translations available from a directory"""
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
    for lang in (CultureInfo.CurrentUICulture, CultureInfo.CurrentUICulture.Parent):
        if lang.IetfLanguageTag in langs:
            current = lang
    if current is not None:
        langs["Windows"] = langs[current.IetfLanguageTag]
    return langs


def set_active_language(language):
    langinfo = get_available_languages().get(language)
    if langinfo is None:
        raise ValueError("LanguageInfo is not available.")
    lang =  langinfo.language.replace("-", "_")
    translation = gettext.translation(app.name, localedir=paths.locale_path(), languages=[language,], fallback=True)
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
    if locale_changed:
        ctypes.windll.kernel32.SetThreadLocale(langinfo.LCID)
    app.current_language = lang
