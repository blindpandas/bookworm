import pytest

from bookworm.database.models import DocumentPositionInfo
from bookworm.document.uri import DocumentUri
from conftest import asset, reader, engine, view

def test_restore_position_for_converted_document(reader, asset, engine):
    """
    Tests if the last read position is correctly saved using the original URI
    for documents that require an internal conversion, such as a file within a ZIP archive.
    """
    original_uri = DocumentUri.from_filename(asset("hello.zip"))
    reader.load(original_uri)

    test_page = 0
    test_pos = 10
    reader.go_to_page(test_page, test_pos)
    reader.save_current_position()

    record = DocumentPositionInfo.query.one()
    assert record is not None
    assert record.last_page == test_page
    assert record.last_position == test_pos
    assert record.uri == original_uri

def test_restore_position_for_directly_supported_document(reader, asset, engine):
    """
    This is a regression test. It ensures that the "restore position" functionality
    for a directly supported format (.epub) remains unaffected by the changes.
    """
    epub_uri = DocumentUri.from_filename(asset("roman.epub"))
    reader.load(epub_uri)

    test_page = 0
    test_pos = 50
    reader.go_to_page(test_page, test_pos)
    reader.save_current_position()

    record = DocumentPositionInfo.query.one()
    assert record is not None
    assert record.last_page == test_page
    assert record.last_position == test_pos
    assert record.uri == epub_uri

def test_document_uri_is_corrected_after_conversion(reader, asset):
    """
    Verifies that the `document.uri` attribute on the reader's in-memory document object
    is correctly updated to the original URI after a conversion has occurred.
    This is important for other features like "Recent Files" or "Pinning".
    """
    original_uri = DocumentUri.from_filename(asset("hello.zip"))
    reader.load(original_uri)

    assert reader.document.uri == original_uri

def test_restore_position_for_mobi_document(reader, asset, engine):
    """
    Provides an additional test case for another convertible format (.mobi)
    to ensure the fix is generic and not specific to ZIP archives.
    """
    original_uri = DocumentUri.from_filename(asset("epub30-spec.mobi"))
    reader.load(original_uri)
    
    test_page = 0
    test_pos = 100
    reader.go_to_page(test_page, test_pos)
    reader.save_current_position()
    
    record = DocumentPositionInfo.query.one()
    assert record is not None
    assert record.last_page == test_page
    assert record.last_position == test_pos
    assert record.uri == original_uri
