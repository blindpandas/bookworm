# coding: utf-8

import wx
from more_itertools import first_true

from bookworm import app, paths
from bookworm.logger import logger

from .localeinfo import LocaleInfo

log = logger.getChild(__name__)


def set_wx_locale(current_locale):
    log.debug(f"Setting wx locale to {current_locale}.")
    wx.GetApp().ResetLocale()
    if hasattr(wx.GetApp(), "AppLocale"):
        del wx.GetApp().AppLocale
    possible_locales = [
        wx.Locale.FindLanguageInfo(lang)
        for lang in (
            current_locale.pylang,
            current_locale.two_letter_language_code,
        )
    ]
    wx_language = first_true(
        possible_locales,
        pred=lambda lc: lc is not None and wx.Locale.IsAvailable(lc.Language),
        default=None,
    )
    if wx_language is None:
        log.exception(
            f"Failed to find corresponding WX language information for locale {current_locale}."
        )
        return
    wx.GetApp().AppLocale = wx.Locale()
    wx.GetApp().AppLocale.AddCatalogLookupPathPrefix(str(paths.locale_path()))
    wx.GetApp().AppLocale.AddCatalog(wx_language.LocaleName)
    wx.GetApp().AppLocale.Init(wx_language.Language)
