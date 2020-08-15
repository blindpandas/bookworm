# coding: utf-8

"""Screen reader and braille output."""

from accessible_output2.outputs.auto import Auto
from bookworm import config
from bookworm.logger import logger


log = logger.getChild(__name__)


_auto_output = None


def announce(message, urgent=False):
    """Speak and braille a message related to UI."""
    global _auto_output
    if not config.conf["general"]["announce_ui_messages"]:
        return
    if _auto_output is None:
        try:
            _auto_output = Auto()
        except AttributeError:
            import shutil, win32com

            shutil.rmtree(win32com.__gen_path__, ignore_errors=True)
            return announce(message, urgent)
    _auto_output.speak(message, interrupt=urgent)
    _auto_output.braille(message)
