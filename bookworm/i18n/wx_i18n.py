# coding: utf-8

import wx
from bookworm import app
from bookworm import paths
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger


log = logger.getChild(__name__)


def set_wx_locale(locale):
    locale_name = locale.pylang
    log.debug(f"Setting wx locale to {locale}.")
    wx_locale = wx.Locale()
    if app.is_frozen:
        wx_locale.AddCatalogLookupPathPrefix(str(paths.locale_path()))
    wx_lang = None
    for loc in (locale, locale.parent, LocaleInfo("en")):
        wx_lang = wx_locale.FindLanguageInfo(locale.pylang)
        if wx_lang:
            try:
                wx_locale.Init(wx_lang.Language)
            except Exception as e:
                log.exception(f"Cannot set wx locale to {locale}.", exc_info=True)
