# coding: utf-8

from bookworm.paths import app_path
from bookworm.platform_services.runtime import SoundFile


_sounds_cache = {}


def __getattr__(sound):
    if sound not in _sounds_cache:
        soundfile = app_path("resources", "soundfiles", f"{sound}.wav")
        _sounds_cache[sound] = SoundFile(str(soundfile))
    return _sounds_cache[sound]
