from __future__ import absolute_import
import os
import ctypes

from .base import Output


class Dolphin(Output):
    """Supports dolphin products."""

    name = "Dolphin"
    lib32 = "dolapi.dll"
    argtypes = {
        "DolAccess_Command": (ctypes.c_wchar_p, ctypes.c_int, ctypes.c_int),
        "DolAccess_Action": (ctypes.c_int,),
    }

    def speak(self, text, interrupt=0):
        if interrupt:
            self.silence()
            # If we don't call this, the API won't let us speak.
        if self.is_active():
            self.lib.DolAccess_Command(text, (len(text) * 2) + 2, 1)

    def silence(self):
        self.lib.DolAccess_Action(141)

    def is_active(self):
        try:
            return self.lib.DolAccess_GetSystem() in (1, 4, 8)
        except:
            return False


output_class = Dolphin
