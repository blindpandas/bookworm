from __future__ import absolute_import

from .base import Output
import appscript


class VoiceOver(Output):

    """Speech output supporting the Apple VoiceOver screen reader."""

    name = "VoiceOver"

    def __init__(self, *args, **kwargs):
        self.app = appscript.app("voiceover")

    def speak(self, text, interrupt=False):
        self.app.output(text)

    def silence(self):
        self.app.output(u"")

    def is_active(self):
        return self.app.isrunning()


output_class = VoiceOver
