# coding: utf-8

import os
import locale as pylocale
import gettext
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from chemical import it
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
    locales = []
    for entry in locale_folders:
        try:
            localeinfo = LocaleInfo(entry)
            locales.append(localeinfo)
        except ValueError:
            continue
    if not any(l.two_letter_language_code == "en" for l in locales):
        locales.append(LocaleInfo("en"))
    _AVAILABLE_LOCALES = {loc.pylang: loc for loc in locales}
    user_locale = get_user_locale()
    if user_locale in locales:
        _AVAILABLE_LOCALES["default"] = user_locale
    elif (parent_locale := user_locale.parent) in locales:
        _AVAILABLE_LOCALES["default"] = parent_locale
    else:
        _AVAILABLE_LOCALES["default"] = LocaleInfo("en")
    return _AVAILABLE_LOCALES


def set_locale(locale_identifier):
    log.debug(f"Setting application locale to {locale_identifier}.")
    available_locales = tuple(get_available_locales().values())
    if locale_identifier in _AVAILABLE_LOCALES:
        localeinfo = _AVAILABLE_LOCALES[locale_identifier]
    else:
        localeinfo = _AVAILABLE_LOCALES["default"]
        config.conf["general"]["language"] = "default"
        config.save()
    lang = localeinfo.pylang
    try:
        translation = gettext.translation(
            app.name, localedir=paths.locale_path(), languages=[lang]
        )
        translation.install(names=["ngettext"])
        os.environ["LANG"] = localeinfo.pylang
        _set_app_locale(localeinfo)
        app.current_language = localeinfo
    except Exception as e:
        if lang != "en":
            log.error(
                f"An error was occured while initializing i18n system.", exc_info=True
            )
        os.environ["LANG"] = "en"
        _set_app_locale(LocaleInfo("en"))
        app.current_language = get_available_locales()["en"]


def setup_i18n():
    set_locale(config.conf["general"]["language"])
    pylocale.setlocale(pylocale.LC_ALL, app.current_language.pylang)
    try:
        set_wx_locale(app.current_language)
    except:
        log.exception("Failed to set wxLocale to the current app locale", exc_info=True)
    try:
        pylocale.getlocale(pylocale.LC_ALL)
    except ValueError:
        pylocale.setlocale(pylocale.LC_ALL, "C")


def is_rtl(lang):
    try:
        return LocaleInfo(lang).is_rtl
    except ValueError:
        return False
