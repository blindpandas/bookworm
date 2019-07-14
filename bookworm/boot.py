# coding: utf-8

"""
Prepares the environment for the application.
"""

import os
import clr
from glob import glob


# XXX Recent versions of Pythonnet does not auto discover
# certain assemblies, so add what we need from the
# Global Assembly Cache (GAC).
# This should be removed, eventually.
import winpaths

_windows_root = winpaths.get_windows()
_speech_assembly = glob(
    os.path.join(
        _windows_root,
        "Microsoft.NET\\assembly\\GAC_MSIL\\",
        "System.Speech\*\System.Speech.dll",
    )
)
clr.AddReference(os.path.abspath(_speech_assembly[0]))
del _windows_root
del _speech_assembly
