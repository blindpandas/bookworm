# coding: utf-8

from . import PLATFORM


if PLATFORM == "win32":
    from ._win32.runtime import system_start_app, is_running_portable, is_high_contrast_active
elif PLATFORM == "linux":
    from ._linux.runtime import system_start_app, is_running_portable, is_high_contrast_active
