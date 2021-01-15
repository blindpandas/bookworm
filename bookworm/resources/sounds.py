# coding: utf-8

from wx.adv import Sound, SOUND_ASYNC
from bookworm.paths import app_path


_sounds_cache = {}


class _SoundObj:
    """Represent a sound file."""

    __slots__ = ["filename", "path", "sound"]

    def __init__(self, filename):
        self.path = app_path("resources", "soundfiles", f"{filename}.wav")
        self.sound = Sound(str(self.path))

    def play(self):
        self.sound.Play(SOUND_ASYNC)


def __getattr__(sound):
    if sound not in _sounds_cache:
        _sounds_cache[sound] = _SoundObj(sound)
    return _sounds_cache[sound]
