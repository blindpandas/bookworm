# coding: utf-8

import sys
import struct
import re


name = "bookworm"
display_name = "Bookworm"
description = "The Universally accessible document reader"
author = "Blind Pandas"
author_email = "info@blindpandas.com"
version = "2022.1b1"
version_ex = "2022.1.0.10"
url = "https://github.com/blindpandas/bookworm"
website = "https://getbookworm.com"
update_url = "https://getbookworm.com/update_info.json"
copyright = f"Copyright (c) 2022 {author} and {display_name} contributors."
exit_code = 0
is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
arch = "x86" if struct.calcsize("P") == 4 else "x64"
debug = False
# The programatic identifier used in file association
prog_id = "bookworm.a11y.reader.1"
# These variables are set upon app initialization
args = extra_args = command_line_mode = as_main = current_language = None

# Version pattern
VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<major>[0-9]+))
        [-_\.]?
        (?P<minor>[0-9]+(?:\.[0-9]+)*)
        (?P<pre>
            [-_\.]?
            (?P<pre_type>(a|b|rc))
            [-_\.]?
            (?P<pre_number>[0-9]+)?
        )?
        (?P<post>
            [-_\.]?
            (?P<post_type>(post))
            [-_\.]?
            (?P<post_number>[0-9]+)?
        )?
    )
"""


def get_version_info(version_string=version):
    pattern = re.compile(
        r"^\s*" + VERSION_PATTERN + r"\s*$", re.VERBOSE | re.IGNORECASE
    )
    mat = pattern.match(version_string)
    if not mat:
        raise ValueError
    return mat.groupdict()
