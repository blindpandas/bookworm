# coding: utf-8


from babel import Locale


def get_user_locale():
    return Locale.default()


def set_app_locale(localeinfo):
    """Perform any necessary operations to set the locale for the app."""