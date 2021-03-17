# coding: utf-8

import wx
from bookworm import app
from bookworm import paths
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger


log = logger.getChild(__name__)


def set_wx_locale(locale):
    wx.GetApp().AppLocale = None
    log.debug(f"Setting wx locale to {locale}.")
    if app.is_frozen:
        wx.Locale.AddCatalogLookupPathPrefix(str(paths.locale_path()))
    candidates = (
        wx.Locale.FindLanguageInfo(l.pylang)
        for l in (locale, locale.parent, LocaleInfo("en"))
    )
    for lang in filter(None, candidates):
        if wx.GetApp().AppLocale:
            del wx.GetApp().AppLocale
        try:
            wx.GetApp().AppLocale = wx.Locale(lang.GetLocaleName())
            if wx.GetApp().AppLocale.IsOk():
                wx.GetApp().AppLocale.AddCatalog("bookworm")
                break
        except:
            log.exception("Failed to set wx Locale", exc_info=True)
