from __future__ import absolute_import
from collections import OrderedDict
from libloader.com import load_com
from .base import Output, OutputError
import pywintypes
import logging

log = logging.getLogger(__name__)

SVSFDefault = 0
SVSFlagsAsync = 1
SVSFPurgeBeforeSpeak = 2
SVSFIsFilename = 4
SVSFIsXML = 8
SVSFIsNotXML = 16
SVSFPersistXML = 32


class SAPI5(Output):
    has_volume = True
    has_rate = True
    has_pitch = True
    min_pitch = -10
    max_pitch = 10
    min_rate = -10
    max_rate = 10
    min_volume = 0
    max_volume = 100
    name = "sapi5"
    priority = 101
    system_output = True

    def __init__(self):
        try:
            self.object = load_com("SAPI.SPVoice")
            self._voices = self._available_voices()
        except pywintypes.com_error:
            raise OutputError
        self._pitch = 0

    def _available_voices(self):
        _voices = OrderedDict()
        for v in self.object.GetVoices():
            _voices[v.GetDescription()] = v
        return _voices

    def list_voices(self):
        return list(self._voices.keys())

    def get_voice(self):
        return self.object.Voice.GetDescription()

    def set_voice(self, value):
        log.debug('Setting SAPI5 voice to "%s"' % value)
        self.object.Voice = self._voices[value]
        # For some reason SAPI5 does not reset audio after changing the voice
        # By setting the audio device after changing voices seems to fix this
        # This was noted from information at:
        # http://lists.nvaccess.org/pipermail/nvda-dev/2011-November/022464.html
        self.object.AudioOutput = self.object.AudioOutput

    def get_pitch(self):
        return self._pitch

    def set_pitch(self, value):
        log.debug("Setting pitch to %d" % value)
        self._pitch = value

    def get_rate(self):
        return self.object.Rate

    def set_rate(self, value):
        log.debug("Setting rate to %d" % value)
        self.object.Rate = value

    def get_volume(self):
        return self.object.Volume

    def set_volume(self, value):
        self.object.Volume = value

    def speak(self, text, interrupt=False):
        if interrupt:
            self.silence()
            # We need to do the pitch in XML here
        textOutput = '<pitch absmiddle="%d">%s</pitch>' % (
            round(self._pitch),
            text.replace("<", "&lt;"),
        )
        self.object.Speak(textOutput, SVSFlagsAsync | SVSFIsXML)

    def silence(self):
        self.object.Speak("", SVSFlagsAsync | SVSFPurgeBeforeSpeak)

    def is_active(self):
        if self.object:
            return True
        return False


output_class = SAPI5
