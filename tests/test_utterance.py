import pytest
from lxml import etree
from bookworm.i18n import LocaleInfo
from bookworm.speechdriver.utterance import SpeechUtterance
from bookworm.speechdriver.element.converter import ssml_converter


def test_utterance_compile_to_ssml():
    ut = SpeechUtterance()
    ut.add_text("Hello")
    ut.add_bookmark("mark1")
    ut.add_audio("file:///C:/myaudio.wav")
    with ut.new_paragraph():
        ut.add_sentence("World")
    ssml_string = ssml_converter.convert(ut, localeinfo=LocaleInfo("en-US"))
    ssml_tree = etree.fromstring(ssml_string)
    assert ssml_tree[0].attrib["name"] == "mark1"
    