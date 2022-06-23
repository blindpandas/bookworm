# coding: utf-8

from . import PLATFORM

if PLATFORM == "win32":
    from ._win32.runtime import (is_high_contrast_active, is_running_portable,
                                 system_start_app)
elif PLATFORM == "linux":
    from ._linux.runtime import (is_high_contrast_active, is_running_portable,
                                 system_start_app)


if PLATFORM == "win32":
    from ._win32.runtime import SoundFile
else:
    from wx.adv import SOUND_ASYNC, Sound

    class SoundFile:
        """Represent a sound file."""

        __slots__ = [
            "path",
            "sound",
        ]

        def __init__(self, filepath):
            self.path = filepath
            self.sound = Sound(self.path)

        def play(self):
            self.sound.Play(SOUND_ASYNC)
