# coding: utf-8

import ctypes
import clr
from System.Globalization import CultureInfo, CultureNotFoundException
from bookworm.i18n import LocaleInfo

def get_user_locale():
    return LocaleInfo(CultureInfo.CurrentUICulture.IetfLanguageTag)


def set_app_locale(localeinfo):
    culture = CultureInfo.GetCultureInfoByIetfLanguageTag(localeinfo.language)
    CultureInfo.CurrentCulture = culture
    CultureInfo.CurrentUICulture = culture
    CultureInfo.DefaultThreadCurrentUICulture = culture
    ctypes.windll.kernel32.SetThreadLocale(culture.LCID)
