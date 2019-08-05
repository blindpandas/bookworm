# coding: utf-8

"""
Prepares the environment for the application.
"""

import sys
import os
import clr
import gettext
from System.IO import FileNotFoundException
from glob import glob


# Make the gettext function _() available in the global namespace, even if no i18n is used
gettext.install("bookworm", names=['ngettext'])


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

# Add CLR assembly-references here
try:
    if not _speech_assembly:
        raise FileNotFoundException
    clr.AddReference(os.path.abspath(_speech_assembly[0]))
except FileNotFoundException:
    import wx
    wx.SafeShowMessage(
        "Unable To Start",
        "Bookworm is unable to start because a key component is missing from your system.\n"
        "Bookworm requires that the .NET Framework v4.0 or a later version is present in the target system.\n"
        "Head over to the following link to download and install the .NET Framework v4.0:\n"
        "https://www.microsoft.com/en-us/download/details.aspx?id=17718"
    )
    sys.exit(1)

del _windows_root
del _speech_assembly
