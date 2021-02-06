# coding: utf-8

"""Provides information and functionality needed at runtime."""


from enum import Enum, auto
from bookworm import app
from bookworm.platform_services.runtime import (
    is_running_portable,
    is_high_contrast_active,
)


__cache = {}


class PackagingMode(Enum):
    Source = auto()
    Installed = auto()
    Portable = auto()


def current_packaging_mode():
    if not app.is_frozen:
        CURRENT_PACKAGING_MODE = PackagingMode.Source
    elif not IS_RUNNING_PORTABLE:
        CURRENT_PACKAGING_MODE = PackagingMode.Installed
    else:
        CURRENT_PACKAGING_MODE = PackagingMode.Portable

MODULE_FUNCS = {
    'CURRENT_PACKAGING_MODE': current_packaging_mode,
    'IS_HIGH_CONTRAST_ACTIVE': is_high_contrast_active,
    'IS_RUNNING_PORTABLE': is_running_portable,
}


def __getattr__(attr):
    if attr not in __cache:
        if attr in MODULE_FUNCS:
            __cache[attr]  = MODULE_FUNCS[attr]()
        else:
            raise AttributeError(f"Module '{__name__}' has no attribute '{attr}'")
    return __cache[attr]