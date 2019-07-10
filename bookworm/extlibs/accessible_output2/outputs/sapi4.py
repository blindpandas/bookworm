from __future__ import absolute_import
from builtins import range
from libloader.com import load_com
from .base import Output

import logging

log = logging.getLogger(__name__)


class Sapi4(Output):

    name = "sapi4"
    priority = 102

    def __init__(self):
        sapi4 = load_com("{EEE78591-FE22-11D0-8BEF-0060081841DE}")
        self._voiceNo = sapi4.Find(0)
        sapi4.Select(self._voiceNo)
        sapi4.Speak(" ")
        self.__object = sapi4
        self._voice_list = self._available_voices()

    def _set_capabilities(self):
        sapi4 = self.__object
        try:
            sapi4.Pitch = sapi4.Pitch
            self._min_pitch = sapi4.MinPitch
            self._max_pitch = sapi4.MaxPitch
            self._has_pitch = True
        except:
            self._min_pitch = 0
            self._max_pitch = 0
            self._has_pitch = False
        try:
            sapi4.Speed = sapi4.Speed
            self._min_rate = sapi4.MinSpeed
            self._max_rate = sapi4.MaxSpeed
            self._has_rate = True
        except:
            self._min_rate = 0
            self._max_rate = 0
            self._has_rate = False
        try:
            sapi4.VolumeLeft = sapi4.VolumeLeft
            self._min_volume = sapi4.MinVolumeLeft
            self._max_volume = sapi4.MaxVolumeLeft
            self._has_volume = True
        except:
            self._min_volume = 0
            self._max_volume = 0
            self._has_volume = False

    def _available_voices(self):
        voice_list = []
        for voice_no in range(1, self.__object.CountEngines):
            voice_list.append(self.__object.ModeName(voice_no))
        return voice_list

    @property
    def available_voices(self):
        return self._voice_list

    def list_voices(self):
        return self.available_voices

    def get_voice(self):
        return self.__object.ModeName(self._voice_no)

    def set_voice(self, value):
        self._voice_no = self.list_voices().index(value) + 1
        self.__object.Select(self._voice_no)
        self.silence()
        self.__object.Speak(" ")
        self._set_capabilities()

    def get_pitch(self):
        if self.has_pitch:
            return self.__object.Pitch

    def set_pitch(self, value):
        if self.has_pitch:
            self.__object.Pitch = value

    def get_rate(self):
        if self.has_rate:
            return self.__object.Speed

    def set_rate(self, value):
        if self.has_rate:
            self.__object.Speed = value

    def get_volume(self):
        if self.has_volume:
            return self.__object.VolumeLeft

    def set_volume(self, value):
        if self.has_volume:
            self.__object.VolumeLeft = value

    @property
    def has_pitch(self):
        return self._has_pitch

    @property
    def has_rate(self):
        return self._has_rate

    @property
    def has_volume(self):
        return self._has_volume

    @property
    def min_pitch(self):
        return self._min_pitch

    @property
    def max_pitch(self):
        return self._max_pitch

    @property
    def min_rate(self):
        return self._min_rate

    @property
    def max_rate(self):
        return self._max_rate

    @property
    def min_volume(self):
        return self._min_volume

    @property
    def max_volume(self):
        return self._max_volume

    def speak(self, text, interrupt=False):
        if interrupt:
            self.silence()
        self.__object.Speak(text)

    def silence(self):
        self.__object.AudioReset()


output_class = Sapi4
