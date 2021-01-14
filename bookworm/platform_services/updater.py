# coding: utf-8

from . import PLATFORM

if PLATFORM == "win32":
    from ._win32.updater import perform_update
elif PLATFORM == "linux":
    from ._linux.updater import perform_update
