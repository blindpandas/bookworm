from __future__ import absolute_import
import ctypes
from .base import Output


class SystemAccess(Output):
    """Supports System Access and System Access Mobile"""

    name = "System Access"
    lib32 = "saapi32.dll"
    argtypes = {"SA_BrlShowTextW": (ctypes.c_wchar_p,), "SA_SayW": (ctypes.c_wchar_p,)}
    priority = 99

    def braille(self, text, **options):
        self.lib.SA_BrlShowTextW(text)

    def speak(self, text, interrupt=False):
        if self.is_active():
            self.dll.SA_SayW(str(text))

    def is_active(self):
        try:
            return self.dll.SA_IsRunning()
        except:
            return False


output_class = SystemAccess
