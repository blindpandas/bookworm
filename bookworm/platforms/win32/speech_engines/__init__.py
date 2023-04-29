# coding: utf-8

from .sapi import SapiSpeechEngine
from .piper import PiperSpeechEngine

TTS_ENGINES = (SapiSpeechEngine, PiperSpeechEngine,)

try:
    from .onecore import OcSpeechEngine
except:
    pass
else:
    TTS_ENGINES = (OcSpeechEngine, *TTS_ENGINES)
