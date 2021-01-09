# coding: utf-8

from . import PLATFORM

if PLATFORM == "win32":
    from ._win32.shell import shell_integrate, shell_disintegrate, get_ext_info
elif PLATFORM == "linux":
    from ._linux.shell import shell_integrate, shell_disintegrate, get_ext_info
