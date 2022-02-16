# coding: utf-8

"""Redirects attribute access to the appropriate image based on whether contrast mode is enabled or not."""

from bookworm.resources import app_icons_data
from bookworm.runtime import IS_HIGH_CONTRAST_ACTIVE


def __getattr__(name):
    img_name = f"_{name}" if not IS_HIGH_CONTRAST_ACTIVE else f"_{name}_hc"
    return getattr(app_icons_data, img_name)
