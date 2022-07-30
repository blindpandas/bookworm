# coding: utf-8

from bookworm.platforms import PLATFORM

if PLATFORM == "win32":
    from bookworm.platforms.win32.user import get_user_locale, set_app_locale
elif PLATFORM == "linux":
    from bookworm.platforms.linux.user import get_user_locale, set_app_locale
