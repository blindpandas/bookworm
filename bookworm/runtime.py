# coding: utf-8

"""Provides information and functionality needed at runtime."""

import clr
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import SystemInformation

import sys
from pathlib import Path
from platform_utils import paths as paths_
from bookworm import app
from bookworm.win_registry import RegKey, Registry


UWP_SERVICES_AVAILABEL = False
try:
    _app_path = Path(paths_.app_path())
    _uwp_services_dll = _app_path / "BookwormUWPServices.dll"
    if not app.is_frozen:
        _uwp_services_dll = (
            Path.cwd()
            / "includes"
            / "BookwormUWPServices"
            / "bin"
            / "Debug"
            / "BookwormUWPServices.dll"
        )
    clr.AddReference(str(_uwp_services_dll))
    UWP_SERVICES_AVAILABEL = True
    del _uwp_services_dll
except Exception as e:
    if '--debug' in sys.argv:
        print(f"Failed to load BookwormUWPServices.dll. {e}")


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
