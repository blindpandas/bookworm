# coding: utf-8

from . import PLATFORM

if PLATFORM == 'win32':
    from ._win32.user import get_user_locale, set_app_locale
elif PLATFORM == 'linux':
    from ._linux.user import get_user_locale, set_app_locale
