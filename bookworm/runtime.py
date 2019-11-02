# coding: utf-8

"""Holds runtime information."""

import sys
from pathlib import Path
from bookworm import app
from bookworm.win_registry import RegKey, Registry


def is_running_portable():
    if not app.is_frozen :
        return False
    unins_key = RegKey(
        Registry.LocalMachine,
        path=fr"Software\Microsoft\Windows\CurrentVersion\Uninstall\{app.name}",
        writable=False
    )
    with unins_key:
        if unins_key.exists and (Path(unins_key.GetValue("InstallLocation")) == Path(sys.executable).parent):
            return False
    return True


def is_high_contrast_active():
    import clr
    clr.AddReference("System.Windows.Forms")
    from System.Windows.Forms import SystemInformation

    return SystemInformation.HighContrast



try:
    IS_RUNNING_PORTABLE = is_running_portable()
except:
    IS_RUNNING_PORTABLE = False

try:
    IS_HIGH_CONTRAST_ACTIVE = is_high_contrast_active()
except:
    IS_HIGH_CONTRAST_ACTIVE = False
