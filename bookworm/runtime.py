# coding: utf-8

"""Provides information and functionality needed at runtime."""


import multiprocessing
from enum import Enum, auto
from bookworm import app
from bookworm.platform_services.runtime import (
    is_running_portable,
    is_high_contrast_active,
)


IS_RUNNING_PORTABLE = is_running_portable()


class PackagingMode(Enum):
    Source = auto()
    Installed = auto()
    Portable = auto()


if not app.is_frozen:
    CURRENT_PACKAGING_MODE = PackagingMode.Source
elif not IS_RUNNING_PORTABLE:
    CURRENT_PACKAGING_MODE = PackagingMode.Installed
else:
    CURRENT_PACKAGING_MODE = PackagingMode.Portable


try:
    IS_HIGH_CONTRAST_ACTIVE = is_high_contrast_active()
except:
    IS_HIGH_CONTRAST_ACTIVE = False


if app.is_frozen:
    IS_IN_MAIN_PROCESS = multiprocessing.parent_process() is None
else:
    IS_IN_MAIN_PROCESS = (multiprocessing.current_process().name == "MainProcess")
