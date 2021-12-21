import pytest
from bookworm.utils import get_url_spans


def test_get_url_spans():
    expected_url_ranges_and_targets = {
        (38, 69): (url1:= 'https://twitter.com/blindpandas'),
        (115, 135): (url2 := 'www.blindpandas.org/'),
        (158, 175): (url3 := 'http://github.com'),
    }
    text = (
        f'Please checkout our twitter stream at {url1}. '
        f'The primary website of our organization is: {url2}\n'
        f'Our code is hosted at {url3}\nPlease check those out.'
    )
    # Internal consistency
    for ((start, end), url_target) in expected_url_ranges_and_targets.items():
        assert text[start:end] == url_target
    url_ranges_and_targets = get_url_spans(text)
    assert dict(url_ranges_and_targets) == expected_url_ranges_and_targets
