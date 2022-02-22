# coding: utf-8

import clr
from System.Globalization import CultureInfo, CultureNotFoundException


import sys
import ctypes
from pathlib import Path
from platform_utils import paths as paths_
from bookworm import app
from bookworm.i18n import LocaleInfo


def get_user_locale():
    return LocaleInfo(CultureInfo.CurrentUICulture.IetfLanguageTag)


def set_app_locale(localeinfo):
    culture = CultureInfo.GetCultureInfoByIetfLanguageTag(localeinfo.language)
    try:
        CultureInfo.CurrentCulture = culture
        CultureInfo.CurrentUICulture = culture
        CultureInfo.DefaultThreadCurrentUICulture = culture
    except TypeError: #105
        pass
    ctypes.windll.kernel32.SetThreadLocale(culture.LCID)
