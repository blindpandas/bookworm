# coding: utf-8

from bookworm.platforms import PLATFORM

if PLATFORM == "win32":
    from bookworm.platforms.win32.shell import (
        shell_disintegrate,
        shell_integrate,
        is_file_type_associated,
    )
elif PLATFORM == "linux":
    from bookworm.platforms.linux.shell import shell_disintegrate, shell_integrate
