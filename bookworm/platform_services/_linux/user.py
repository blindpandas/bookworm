# coding: utf-8


from babel import Locale
from bookworm.i18n import LocaleInfo


def get_user_locale():
    return LocaleInfo.from_babel_locale(Locale.default())


def set_app_locale(localeinfo):
    """Perform any necessary operations to set the locale for the app."""
