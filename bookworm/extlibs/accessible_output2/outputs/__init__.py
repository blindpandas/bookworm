from __future__ import absolute_import
import platform

if platform.system() == "Windows":
    from . import nvda
    from . import jaws
    from . import sapi5
    from . import window_eyes
    from . import system_access
    from . import dolphin
    from . import pc_talker

    # import sapi4

if platform.system() == "Darwin":
    from . import voiceover

if platform.system() == "Linux":
    from . import e_speak

from . import auto
