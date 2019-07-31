# coding: utf-8

import sys
import os
import struct
import regex as re


name = "bookworm"
is_frozen = hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS')
display_name = "Bookworm"
localized_name = _("Bookworm")
author = "Musharraf Omer"
author_email = "ibnomer2011@hotmail.com"
version = "0.1b1"
version_ex = "0.1.0.0"
url = "https://github.com/mush42/bookworm/"
website = "https://mush42.github.io/bookworm/"
update_url = "http://localhost:5000/current_version.json"
copyright = f"Copyright (c) 2019 {author}."
arch = "x86" if struct.calcsize("P") == 4 else "x64"
debug = False

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
    pattern = re.compile(r"^\s*" + VERSION_PATTERN + r"\s*$", re.VERBOSE | re.IGNORECASE)
    mat = pattern.match(version_string, concurrent=True)
    if not mat:
        raise ValueError
    return mat.groupdict()


