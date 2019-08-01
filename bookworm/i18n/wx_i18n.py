import wx
from bookworm import app


def set_wx_language(lang, locale_path):
    wx_locale = wx.Locale()
    if app.is_frozen:
        wx_locale.AddCatalogLookupPathPrefix(locale_path)
    wx_lang = locale.FindLanguageInfo(lang)
    if not wx_lang and '_' in lang:
        wx_lang = locale.FindLanguageInfo(lang.split('_')[0])
    if wx_lang and not locale.IsAvailable(wx_lang.Language):
        wx_lang = None
    if wx_lang:
        try:
            wx_locale.Init(lang, wx_lang)
        except:
            pass
