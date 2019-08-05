# coding: utf-8

import sys
import os


name = "bookworm"
is_frozen = hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS")
display_name = "Bookworm"
localized_name = _("Bookworm")
author = "Musharraf Omer"
author_email = "ibnomer2011@hotmail.com"
version = "0.1b1"
version_ex = "0.1.0.0"
url = "https://github.com/mush42/bookworm/"
website = "https://mush42.github.io/bookworm/"
copyright = f"Copyright (c) 2019 {author}."
debug = False

# About Message
about_msg = f"""
{localized_name}
Version: {version}
Website: {website}

{localized_name} is an ACCESSIBLEebook reader that enables blind and visually impaired individuals to read e-books in an easy, accessible, and hassle-free manor. It is being developed by {author}.

{copyright}
This software is offered to you under the terms of The MIT license.
You can view the license text from the help menu.

As a blind developer, my responsibility is to develop applications that provide independence for me, and for my fellow blind friends allover the world. So, if you've found Bookworm useful in any way, please help me in making Bookworm better for you and for others. At this initial stage, I want you to tell me about any errors you may encounter during your use of Bookworm. To do so, open a new issue with the details of the error at [the issue tracker](https://github.com/mush42/bookworm/issues/). Your help is greatly appreciated.

To keep yourself updated with the latest news about Bookworm, you can visit Bookworm's website at: ({website}). You can also follow me, {author}, at (@mush42) on Twitter
"""
