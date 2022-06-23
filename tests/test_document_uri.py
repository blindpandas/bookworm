from pathlib import Path

import pytest

from bookworm.document.uri import DocumentUri


def test_uri_from_filename(asset):
    filename = Path(asset("The Diary of a Nobody.epub")).resolve()
    uri = DocumentUri.from_filename(str(filename))
    assert uri.format == 'epub'
    assert Path(uri.path).resolve() == filename
    assert uri.openner_args == {}
    as_str = uri.to_uri_string()
    parsed_uri = uri.from_uri_string(as_str)
    assert uri.path == parsed_uri.path
    assert uri == parsed_uri
