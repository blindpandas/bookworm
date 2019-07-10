from __future__ import absolute_import
import win32gui
from libloader.com import load_com
from .base import Output, OutputError
import pywintypes


class WindowEyes(Output):
    """Speech output supporting the WindowEyes screen reader"""

    name = "Window-Eyes"

    def __init__(self, *args, **kwargs):
        super(WindowEyes, self).__init__(*args, **kwargs)
        try:
            self.object = load_com("gwspeak.speak")
        except pywintypes.com_error:
            raise OutputError

    def speak(self, text, interrupt=0):
        if interrupt:
            self.silence()
        self.object.SpeakString(text)

    def silence(self):
        self.object.Silence()

    def is_active(self):
        try:
            return win32gui.FindWindow("GWMExternalControl", "External Control") != 0
        except:
            return False


output_class = WindowEyes
