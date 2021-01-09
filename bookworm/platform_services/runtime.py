# coding: utf-8

import sys

PLATFORM = sys.platform

if PLATFORM == 'win32':
    from ._win32.runtime import is_running_portable, is_high_contrast_active
elif PLATFORM == 'linux':
    from ._linux.runtime import is_running_portable, is_high_contrast_active
