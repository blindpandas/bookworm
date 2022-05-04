# coding: utf-8

"""Screen reader and braille output."""

from cytolk import tolk
from bookworm import config
from bookworm.signals import reading_position_change
from bookworm.logger import logger


log = logger.getChild(__name__)


def announce(message, urgent=False):
    """Speak and braille a message related to UI."""
    if not config.conf["general"]["announce_ui_messages"]:
        return
    # always using a context manager should probably be cheap
    # if it ends up not being the case, we can change it
    with tolk.tolk():
        tolk.output(message, urgent)

@reading_position_change.connect
def announce_new_reading_position(sender, position, **kwargs):
    if text_to_announce := kwargs.get("text_to_announce"):
        announce(text_to_announce, urgent=True)
