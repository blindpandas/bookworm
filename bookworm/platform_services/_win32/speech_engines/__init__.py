# coding: utf-8

from .onecore import OcSpeechEngine
from .sapi import SapiSpeechEngine

TTS_ENGINES = (OcSpeechEngine, SapiSpeechEngine,)
