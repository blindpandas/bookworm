# coding: utf-8

import wx
from bookworm import app
from bookworm import paths
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger


log = logger.getChild(__name__)


def set_wx_locale(current_locale):
    log.debug(f"Setting wx locale to {current_locale}.")
    if hasattr(wx.GetApp(), "AppLocale"):
        del wx.GetApp().AppLocale
    current_language = current_locale.pylang
    wx_language = wx.Locale.FindLanguageInfo(current_language)
    if wx_language is None:
        log.exception(f"Failed to find corresponding WX language information for locale {current_locale}.")
        return
    wx.GetApp().AppLocale = wx.Locale()
    wx.GetApp().AppLocale.AddCatalogLookupPathPrefix(str(paths.locale_path()))
    wx.GetApp().AppLocale.AddCatalog(wx_language.LocaleName)
    wx.GetApp().AppLocale.Init(wx_language.Language)
