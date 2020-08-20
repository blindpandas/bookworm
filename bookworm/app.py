# coding: utf-8

import sys
import os
import struct
import re


name = "bookworm"
display_name = "Bookworm"
author = "Musharraf Omer"
author_email = "ibnomer2011@hotmail.com"
version = "0.2"
version_ex = "0.2.0.0"
url = "https://github.com/mush42/bookworm/"
website = "https://mush42.github.io/bookworm/"
update_url = "https://mush42.github.io/bookworm/current_version.json"
copyright = f"Copyright (c) 2020 {author} and {display_name} contributors."
is_frozen = hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS")
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
