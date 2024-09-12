import pytest

from bookworm.otau import UpdateChannel


def test_is_not_valid_identifier():
    with pytest.raises(TypeError):
        channel = UpdateChannel('test')


def test_is_valid_identifier():
    valid_identifiers = ('', 'a', 'b', 'rc')
    for identifier in valid_identifiers:
        channel = UpdateChannel(identifier)


def test_is_major_version():
    c = UpdateChannel('')
    assert c.is_major == True
