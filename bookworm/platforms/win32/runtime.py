# coding: utf-8

import clr
from ctypes import windll, wintypes, byref
import sys
import winsound
from functools import lru_cache
from pathlib import Path
from subprocess import list2cmdline

import winpaths
from bookworm import app

from . import shellapi
from .win_registry import RegKey, RegRoots


SPI_GETHIGHCONTRAST = 0x0042
PLAYER_FLAGS = winsound.SND_ASYNC | winsound.SND_FILENAME
UWP_SERVICES_AVAILABEL = False



class SoundFile:
    """Represent a sound file."""

    __slots__ = [
        "path",
    ]

    def __init__(self, filepath):
        self.path = filepath

    def play(self):
        winsound.PlaySound(self.path, PLAYER_FLAGS)


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
    try:
        unins_key = RegKey(
            RegRoots.LocalMachine,
            path=rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{app.name}",
            writable=False,
        )
    except OSError:
        return True
    else:
        unins_path_value = unins_key.get_value("InstallLocation")
        if Path(unins_path_value).resolve() == Path(sys.executable).parent.resolve():
            return False
    return True


def is_high_contrast_active():
    val = wintypes.BOOL()
    windll.user32.SystemParametersInfoW(SPI_GETHIGHCONTRAST, 0, byref(val), 0)
    return bool(val.value)
