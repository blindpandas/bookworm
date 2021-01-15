# coding: utf-8


import clr

clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import SystemInformation

import sys
import winpaths
from subprocess import list2cmdline
from functools import lru_cache
from pathlib import Path
from bookworm import app
from platform_utils.paths import app_path
from . import shellapi
from .win_registry import RegKey, Registry


UWP_SERVICES_AVAILABEL = False
try:
    _app_path = Path(app_path())
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
    if "--debug" in sys.argv:
        print(f"Failed to load BookwormUWPServices.dll. {e}")


def system_start_app(executable, args):
    shellapi.ShellExecute(None, None, executable, list2cmdline(args), None, 1)


@lru_cache(maxsize=10)
def reference_gac_assembly(glob_pattern: str):
    """
    Locate an assembly from the GAC and reference it.

    Recent versions of Pythonnet does not auto discover certain .NET framework
    assemblies, so add what we need from the global Assembly Cache (GAC).
    """
    gac_home = "Microsoft.NET\\assembly\\GAC_MSIL\\"
    assemblies = tuple(Path(winpaths.get_windows(), gac_home).rglob(glob_pattern))
    if not assemblies:
        raise OSError(f"Could not find assembily: {glob_pattern}")
    clr.AddReference(str(assemblies[0]))


def is_running_portable():
    if not app.is_frozen:
        return False
    unins_key = RegKey(
        Registry.LocalMachine,
        path=fr"Software\Microsoft\Windows\CurrentVersion\Uninstall\{app.name}",
        writable=False,
    )
    with unins_key:
        if unins_key.exists and (
            Path(unins_key.GetValue("InstallLocation")).resolve()
            == Path(sys.executable).parent.resolve()
        ):
            return False
    return True


def is_high_contrast_active():
    return SystemInformation.HighContrast
