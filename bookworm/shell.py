# coding: utf-8

from bookworm.platforms import PLATFORM

if PLATFORM == "win32":
    from bookworm.platforms.win32.shell import shell_disintegrate, shell_integrate
elif PLATFORM == "linux":
    from bookworm.platforms.linux.shell import shell_disintegrate, shell_integrate
