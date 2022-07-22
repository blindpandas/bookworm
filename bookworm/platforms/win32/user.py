# coding: utf-8


import clr
from System.Globalization import CultureInfo, CultureNotFoundException



import sys
import ctypes
from ctypes.wintypes import BOOL, DWORD, LPCVOID, LPWSTR, LPCWSTR
import logging

from bookworm import app
from bookworm import typehints as t
from bookworm.i18n.localeinfo import LocaleInfo


# https://msdn.microsoft.com/en-us/library/windows/desktop/dd318124%28v=vs.85%29.aspx
MUI_LANGUAGE_ID = 4
MUI_LANGUAGE_NAME = 8


GetUserPreferredUILanguages = ctypes.windll.kernel32.GetUserPreferredUILanguages
SetThreadPreferredUILanguages = ctypes.windll.kernel32.SetThreadPreferredUILanguages


GetUserPreferredUILanguages.argtypes = [
    DWORD,
    ctypes.POINTER(ctypes.c_ulong),
    LPCVOID,
    ctypes.POINTER(ctypes.c_ulong),
]
GetUserPreferredUILanguages.restype = BOOL

SetThreadPreferredUILanguages.argtypes = [
    DWORD,
    LPCVOID,
    ctypes.POINTER(ctypes.c_ulong),
]
SetThreadPreferredUILanguages.restype = BOOL


def get_preferred_languages() -> t.Iterable[str]:
    """
    https://raw.githubusercontent.com/EDCD/EDMarketConnector/main/l10n.py
    Return a list of preferred language codes.

    Returned data is in RFC4646 format (i.e. "lang[-script][-region]")
    Where lang is a lowercase 2 alpha ISO 693-1 or 3 alpha ISO 693-2 code
    Where script is a capitalized 4 alpha ISO 15924 code
    Where region is an uppercase 2 alpha ISO 3166 code

    :return: The preferred language list
    """

    def wszarray_to_list(array):
        offset = 0
        while offset < len(array):
            sz = ctypes.wstring_at(ctypes.addressof(array) + offset * 2)
            if sz:
                yield sz
                offset += len(sz) + 1
            else:
                break

    num = ctypes.c_ulong()
    size = ctypes.c_ulong(0)
    languages = []
    if (
        GetUserPreferredUILanguages(
            MUI_LANGUAGE_NAME, ctypes.byref(num), None, ctypes.byref(size)
        )
        and size.value
    ):
        buf = ctypes.create_unicode_buffer(size.value)

        if GetUserPreferredUILanguages(
            MUI_LANGUAGE_NAME, ctypes.byref(num), ctypes.byref(buf), ctypes.byref(size)
        ):
            languages = wszarray_to_list(buf)
    return tuple(languages)


def get_user_locale():
    return LocaleInfo(get_preferred_languages()[0])


def set_app_locale(localeinfo):
    ietf_tag = localeinfo.ietf_tag
    langs = list(get_preferred_languages())
    try:
        langs.remove(ietf_tag)
    except ValueError:
        pass
    langs.insert(0, localeinfo.two_letter_language_code)
    langs.insert(0, ietf_tag)
    ulangs = "\0".join(langs)
    buf = ctypes.create_unicode_buffer("ar-SD", size=len(ulangs) + 2)
    num_langs = ctypes.c_ulong(len(langs))
    if not SetThreadPreferredUILanguages(
        MUI_LANGUAGE_NAME,
        ctypes.byref(buf),
        ctypes.byref(num_langs)
    ):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not set default thread locale to {ietf_tag}")
