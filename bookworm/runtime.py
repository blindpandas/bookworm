# coding: utf-8

"""Provides information and functionality needed at runtime."""


from bookworm.platform_services.runtime import is_running_portable, is_high_contrast_active


IS_RUNNING_PORTABLE = is_running_portable()

try:
    IS_HIGH_CONTRAST_ACTIVE = is_high_contrast_active()
except:
    IS_HIGH_CONTRAST_ACTIVE = False


