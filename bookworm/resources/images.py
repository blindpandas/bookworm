# coding: utf-8

"""Redirects attribute access to the appropriate image based on whether contrast mode is enabled or not."""

from bookworm.runtime import IS_HIGH_CONTRAST_ACTIVE
from bookworm.resources import image_data


def __getattr__(name):
    img_name = f"_{name}" if not IS_HIGH_CONTRAST_ACTIVE else f"_{name}_hc"
    return getattr(image_data, img_name)
