import time
from bookworm.speech.utterance import SpeechUtterance
from bookworm.speech.engines.onecore import OcSpeechEngine as E

e= E()
e.synth.BookmarkReached += lambda s, b: print(f"Reached bookmark: {b}")
u = SpeechUtterance()
u.add_text("Hello world")
u.add_bookmark("go-oc")
u.add_text("Gootta" * 3)
