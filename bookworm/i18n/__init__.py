from bookworm import app
from bookworm import config
from bookworm.logger import logger
from .core import *
from .wx_i18n import set_wx_language


log = logger.getChild(__name__)


def setup_i18n():
    lang = config.conf["general"]["language"]
    if lang not in get_available_languages():
        log.error(f"The configured language '{lang}' is not available.")
        return
    log.info(f"Setting application language to {lang}.")
    set_active_language(lang)
    set_wx_language(app.current_language)
