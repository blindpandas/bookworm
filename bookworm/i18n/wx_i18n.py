# coding: utf-8

import wx
from bookworm import app
from bookworm import paths
from bookworm.logger import logger


log = logger.getChild(__name__)


def set_wx_language(lang):
    log.debug(f"Setting wx locale to {lang}.")
    if app.is_frozen:
        wx_locale.AddCatalogLookupPathPrefix(paths.locale_path())
    wx_locale = wx.Locale()
    wx_lang = wx_locale.FindLanguageInfo(lang)
    if not wx_lang and "_" in lang:
        wx_lang = wx_locale.FindLanguageInfo(lang.split("_")[0])
    if wx_lang and not wx_locale.IsAvailable(wx_lang.Language):
        wx_lang = None
    if wx_lang:
        try:
            wx_locale.Init(wx_lang.Language)
        except:
            log.error(f"Cannot set wx locale to {lang}.")
