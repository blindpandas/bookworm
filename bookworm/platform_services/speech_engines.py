# coding: utf-8

from . import PLATFORM

if PLATFORM == "win32":
    from ._win32.speech_engines import TTS_ENGINES
elif PLATFORM == "linux":
    from ._linux.speech_engines import TTS_ENGINES
