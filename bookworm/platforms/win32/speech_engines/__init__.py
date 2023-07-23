# coding: utf-8

from .sapi import SapiSpeechEngine

TTS_ENGINES = (SapiSpeechEngine,)

try:
    from .piper import PiperSpeechEngine
except:
    raise
else:
    TTS_ENGINES = (*TTS_ENGINES, PiperSpeechEngine)


try:
    from .onecore import OcSpeechEngine
except:
    pass
else:
    TTS_ENGINES = (OcSpeechEngine, *TTS_ENGINES)
