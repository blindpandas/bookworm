# coding: utf-8

"""Screen reader and braille output."""

import sys
import shutil
import win32com

from accessible_output2.outputs.auto import Auto

from bookworm import config
from bookworm.utils import restart_application
from bookworm.logger import logger
from bookworm.signals import reading_position_change

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
        except (AttributeError, ImportError):
            shutil.rmtree(win32com.__gen_path__, ignore_errors=True)
            restart_application()
    _auto_output.speak(message, interrupt=urgent)
    _auto_output.braille(message)


@reading_position_change.connect
def announce_new_reading_position(sender, position, **kwargs):
    if text_to_announce := kwargs.get("text_to_announce"):
        announce(text_to_announce, urgent=True)
