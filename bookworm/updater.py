# coding: utf-8

from bookworm.platforms import PLATFORM

if PLATFORM == "win32":
    from bookworm.platforms.win32.updater import perform_update
elif PLATFORM == "linux":
    from bookworm.platforms.linux.updater import perform_update
