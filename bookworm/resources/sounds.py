# coding: utf-8

import winsound
from bookworm.paths import app_path


PLAYER_FLAGS = winsound.SND_ASYNC | winsound.SND_FILENAME
_sounds_cache = {}


class _SoundObj:
    """Represent a sound file."""

    __slots__ = ["filename", "path", "sound"]

    def __init__(self, filename):
        self.path = app_path("resources", "soundfiles", f"{filename}.wav")

    def play(self):
        winsound.PlaySound(str(self.path), PLAYER_FLAGS)


def __getattr__(sound):
    if sound not in _sounds_cache:
        _sounds_cache[sound] = _SoundObj(sound)
    return _sounds_cache[sound]
