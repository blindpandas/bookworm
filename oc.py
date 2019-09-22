from bookworm.speech.engines.onecore.oc_engine import OnecoreSpeechEngine as OS, OnecoreSpeechUtterance as US, EngineEvents as EE

e = OS()
u = US()
u.add_sentence("OK")
u.add_bookmark("my-book-mark")
u.add_text("Hey you" * 5)
e.bind(EE.bookmark_reached, lambda b: print(b))
e.speak(u)
