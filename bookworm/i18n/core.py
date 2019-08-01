import ctypes
import os
import gettext
import locale

"""We should move to a dotnet based implementation."""
"""I18n support is versatile, and we depend on it anyway."""

# a few Windows locale constants
LOCALE_SLANGUAGE = 0x2
LOCALE_SLANGDISPLAYNAME = 0x6F
BUFFSIZE = 1024


def locale_name_to_LCID(locale_name):
    locale_name = locale.normalize(locale_name)
    if "." in locale_name:
        locale_name = locale_name.split(".")[0]
    func_locale_nameToLCID = getattr(ctypes.windll.kernel32, "localeNameToLCID", None)
    if func_locale_nameToLCID is not None:
        locale_name = locale_name.replace("_", "-")
        LCID = func_locale_nameToLCID(locale_name, 0)
    else:
        LCList = [
            x[0] for x in locale.windows_locale.items() if x[1] == locale_name
        ]
        if len(LCList) > 0:
            LCID = LCList[0]
        else:
            LCID = 0
    return LCID


def language_description(language):
    """Determine the label of the language"""
    LCID = locale_name_to_LCID(language)
    if LCID == 0:
        return None
    buffer = ctypes.create_unicode_buffer(BUFFSIZE)
    res = 0
    if "_" not in language:
        res = ctypes.windll.kernel32.GetLocaleInfoW(
            LCID, LOCALE_SLANGDISPLAYNAME, buffer, BUFFSIZE
        )
    if res == 0:
        res = ctypes.windll.kernel32.GetLocaleInfoW(
            LCID, LOCALE_SLANGUAGE, buffer, BUFFSIZE
        )
    return buffer.value


def available_languages(locale_dir, app_name):
    """List the translations available from a directory"""
    dirs = [i for i in os.listdir(locale_dir) if not i.startswith(".")]
    langs = sorted(
        ["en"]
        + [
            i
            for i in dirs
            if os.path.isfile(
                os.path.join(locale_dir, "%s/LC_MESSAGES/%s.mo" % (i, app_name))
            )
        ]
    )
    langs = set(langs)
    result = dict()
    for l in langs:
        result[l] = dict(LCID=locale_name_to_LCID(l))
        description = language_description(l)
        result[l]["language"] = description if description else l
    if "Windows" not in result:
        result["Windows"] = dict(language="User default, Windows")
    return result


def set_active_language(app_name, locale_dir, lang):
    try:
        if lang == "Windows":
            LCID = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            lang = locale.windows_locale[LCID]
            translation = gettext.translation(
                app_name, localedir=locale_dir, languages=[lang]
            )
            translation.install(True, names=["ngettext"])
        else:
            translation = gettext.translation(
                app_name, localedir=locale_dir, languages=[lang]
            )
            translation.install(True, names=["ngettext"])
            locale_changed = False
            try:
                locale.setlocale(locale.LC_ALL, lang)
                locale_changed = True
            except:
                pass
            if not locale_changed and "_" in lang:
                try:
                    locale.setlocale(locale.LC_ALL, lang.split("_")[0])
                except:
                    pass
            LCID = locale_name_to_LCID(lang)
            ctypes.windll.kernel32.SetThreadLocale(LCID)
            return lang
    except IOError:
        gettext.install(app_name, names=["ngettext"])
