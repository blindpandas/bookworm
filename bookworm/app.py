# coding: utf-8

import sys
import struct
import re


name = "bookworm"
display_name = "Bookworm"
description = "The Universally accessible document reader"
author = "Blind Pandas"
author_email = "info@blindpandas.com"
version = "0.4b1"
version_ex = "0.4.0.1"
url = "https://github.com/blindpandas/bookworm"
website = "https://blindpandas.com/bookworm/"
update_url = "https://blindpandas.com/bookworm/current_version.json"
copyright = f"Copyright (c) 2021 {author} and {display_name} contributors."
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
