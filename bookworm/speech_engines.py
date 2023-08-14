# coding: utf-8

from bookworm.platforms import PLATFORM

if PLATFORM == "win32":
    from bookworm.platforms.win32.speech_engines import TTS_ENGINES
elif PLATFORM == "linux":
    from bookworm.platforms.linux.speech_engines import TTS_ENGINES
