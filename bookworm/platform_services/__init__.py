# coding: utf-8

import sys

PLATFORM = sys.platform

if PLATFORM == 'win32':
    from ._win32 import *
elif PLATFORM == 'linux':
    from ._linux import *
