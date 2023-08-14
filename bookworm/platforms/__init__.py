# coding: utf-8

import sys

PLATFORM = sys.platform


if PLATFORM == "win32":
    from .win32 import check_runtime_components
else:
    from .linux import check_runtime_components
