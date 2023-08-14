# coding: utf-8

from .sapi import SapiSpeechEngine

TTS_ENGINES = (SapiSpeechEngine,)

try:
    from .onecore import OcSpeechEngine
except:
    pass
else:
    TTS_ENGINES = (OcSpeechEngine, *TTS_ENGINES)
