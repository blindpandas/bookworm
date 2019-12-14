# coding: utf-8

"""Holds runtime information."""

import clr
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import SystemInformation

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
        if unins_key.exists and (Path(unins_key.GetValue("InstallLocation")).resolve() == Path(sys.executable).parent.resolve()):
            return False
    return True


def is_high_contrast_active():
    return SystemInformation.HighContrast



IS_RUNNING_PORTABLE = is_running_portable()

try:
    IS_HIGH_CONTRAST_ACTIVE = is_high_contrast_active()
except:
    IS_HIGH_CONTRAST_ACTIVE = False
