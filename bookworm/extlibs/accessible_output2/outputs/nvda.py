from __future__ import absolute_import
import os
import platform
import ctypes

from platform_utils import paths
from libloader import load_library
from .base import Output


class NVDA(Output):
    """Supports The NVDA screen reader"""

    name = "NVDA"
    lib32 = "nvdaControllerClient32.dll"
    lib64 = "nvdaControllerClient64.dll"
    argtypes = {
        "nvdaController_brailleMessage": (ctypes.c_wchar_p,),
        "nvdaController_speakText": (ctypes.c_wchar_p,),
    }

    def is_active(self):
        try:
            return self.lib.nvdaController_testIfRunning() == 0
        except:
            return False

    def braille(self, text, **options):
        self.lib.nvdaController_brailleMessage(text)

    def speak(self, text, interrupt=False):
        if interrupt:
            self.silence()
        self.lib.nvdaController_speakText(text)

    def silence(self):
        self.lib.nvdaController_cancelSpeech()


output_class = NVDA
