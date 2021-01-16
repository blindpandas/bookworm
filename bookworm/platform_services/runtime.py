# coding: utf-8

from . import PLATFORM


if PLATFORM == "win32":
    from ._win32.runtime import system_start_app, is_running_portable, is_high_contrast_active
elif PLATFORM == "linux":
    from ._linux.runtime import system_start_app, is_running_portable, is_high_contrast_active


if PLATFORM == 'win32':
    from ._win32.runtime import SoundFile
else:
    from wx.adv import Sound, SOUND_ASYNC

    class SoundFile:
        """Represent a sound file."""

        __slots__ = ["path", "sound",]

        def __init__(self, filepath):
            self.path = filepath
            self.sound = Sound(self.path)

        def play(self):
            self.sound.Play(SOUND_ASYNC)

