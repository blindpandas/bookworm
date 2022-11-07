import pytest
from lxml import etree
from bookworm.speechdriver.utterance import SpeechUtterance


def test_utterance_compile_to_ssml():
    ut = SpeechUtterance()
    ut.add_text("Hello")
    ut.add_bookmark("mark1")
    ut.add_audio("file:///C:/myaudio.wav")
    with ut.new_paragraph():
        ut.add_sentence("World")
    ssml_string = ut.compile_to_ssml()
    ssml_tree = etree.fromstring(ssml_string)
    assert ssml_tree[0].attrib["name"] == "mark1"
    