from bookworm import app
from bookworm import config
from bookworm import paths
from bookworm.logger import logger
from .core import *
from .wx_i18n import set_wx_language


log = logger.getChild(__name__)


def setup_i18n():
    locale_dir = str(paths.locale_path())
    lang = config.conf["general"]["language"]
    log.info(f"Setting application language to {lang}, {language_description(lang)}.")
    current_language = set_active_language(app.name, locale_dir, lang)
    if current_language is not None:
        app.current_language = current_language
        set_wx_language(current_language, locale_dir)
