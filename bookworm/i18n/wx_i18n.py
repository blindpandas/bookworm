import wx
from bookworm import app
from bookworm import paths


def set_wx_language(lang):
    wx_locale = wx.Locale()
    if app.is_frozen:
        wx_locale.AddCatalogLookupPathPrefix(paths.locale_path())
    wx_lang = wx_locale.FindLanguageInfo(lang)
    if not wx_lang and '_' in lang:
        wx_lang = wx_locale.FindLanguageInfo(lang.split('_')[0])
    if wx_lang and not wx_locale.IsAvailable(wx_lang.Language):
        wx_lang = None
    if wx_lang:
        try:
            wx_locale.Init(lang, wx_lang)
        except:
            pass
