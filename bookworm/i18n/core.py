# coding: utf-8

import os
import gettext
import locale
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from chemical import it
from babel import UnknownLocaleError, Locale, parse_locale, default_locale
from bookworm import app
from bookworm import paths
from bookworm import config
from bookworm.platform_services.user import (
    get_user_locale,
    set_app_locale as _set_app_locale,
)
from bookworm.signals import app_started
from bookworm.logger import logger
from .localeinfo import LocaleInfo
from .wx_i18n import set_wx_locale


log = logger.getChild(__name__)

_AVAILABLE_LOCALES = None


def get_available_locales(force_update=False):
    """List the translations available from a directory"""
    global _AVAILABLE_LOCALES
    if _AVAILABLE_LOCALES and not force_update:
        return _AVAILABLE_LOCALES
    folders = [item for item in Path(paths.locale_path()).iterdir() if item.is_dir()]
    locale_folders = [
        entry.name
        for entry in folders
        if entry.joinpath(f"LC_MESSAGES/{app.name}.mo").is_file()
    ]
    user_locale = get_user_locale()
    parent_locale = user_locale.parent
    if user_locale.pylang in locale_folders:
        locale_folders.remove(user_locale.pylang)
        locale_folders.insert(0, user_locale.pylang)
    elif parent_locale.pylang in locale_folders:
        locale_folders.remove(parent_locale.pylang)
        locale_folders.insert(0, parent_locale.pylang)
    elif not it(locale_folders).any(lambda l: l.startswith("en")):
        locale_folders.insert(0, "en")
    locales = []
    for entry in locale_folders:
        try:
            localeinfo = LocaleInfo(entry)
            locales.append(localeinfo)
        except ValueError:
            continue
    _AVAILABLE_LOCALES = {loc.pylang: loc for loc in locales}
    _AVAILABLE_LOCALES["default"] = locales[0]
    return _AVAILABLE_LOCALES


def set_locale(locale_identifier):
    log.debug(f"Setting application locale to {locale_identifier}.")
    available_locales = tuple(get_available_locales().values())
    localeinfo = LocaleInfo(locale_identifier)
    if localeinfo not in available_locales:
        localeinfo = (
            localeinfo.parent
            if localeinfo.parent in available_locales
            else _AVAILABLE_LOCALES["default"]
        )
    lang = localeinfo.pylang
    try:
        translation = gettext.translation(
            app.name, localedir=paths.locale_path(), languages=[lang]
        )
        translation.install(names=["ngettext"])
        locale.setlocale(locale.LC_ALL, lang)
        app_started.connect(lambda s: set_wx_locale(localeinfo), weak=False)
        _set_app_locale(localeinfo)
        app.current_language = localeinfo
        os.environ["LANG"] = localeinfo.pylang
    except Exception as e:
        if lang != "en":
            log.error(
                f"An error was occured while initializing i18n system.", exc_info=True
            )
        _set_app_locale(LocaleInfo("en"))
        app.current_language = get_available_locales()["en"]
        os.environ["LANG"] = "en"


def setup_i18n():
    set_locale(config.conf["general"]["language"])


def is_rtl(lang):
    try:
        return LocaleInfo(lang).locale.text_direction == "RTL"
    except ValueError:
        return False
