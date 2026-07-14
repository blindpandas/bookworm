from types import SimpleNamespace

from bookworm.database.models import DocumentPositionInfo
from bookworm.document import SINGLE_PAGE_DOCUMENT_PAGER, Section
from bookworm.document.uri import DocumentUri
from bookworm.structured_text import TextRange


def make_section(title, start, stop):
    return Section(
        title=title,
        pager=SINGLE_PAGE_DOCUMENT_PAGER,
        text_range=TextRange(start, stop),
    )


def test_set_active_section_can_skip_view_section_change(reader):
    current_section = make_section("Current", 0, 10)
    target_section = make_section("Target", 20, 40)
    reader.document = SimpleNamespace(has_toc_tree=lambda: True)
    reader._EBookReader__state = {"active_section": current_section}

    reader.set_active_section(target_section, update_view=False)

    assert reader.active_section is target_section
    assert reader.view.state_on_section_change is None


def test_go_to_first_of_section_moves_to_section_start_in_single_page_document(reader):
    section = make_section("Target", 20, 40)
    reader.document = SimpleNamespace(is_single_page_document=lambda: True)
    reader._EBookReader__state = {
        "active_section": section,
        "current_page_index": section.pager.first,
    }
    reader.view.get_containing_line = lambda _position: (18, 30)

    reader.go_to_first_of_section()

    assert reader.view.get_insertion_point() == 18


def test_go_to_first_of_section_ignores_missing_single_page_section_range(reader):
    section = Section(title="Target", pager=SINGLE_PAGE_DOCUMENT_PAGER)
    reader.document = SimpleNamespace(is_single_page_document=lambda: True)
    reader._EBookReader__state = {
        "active_section": section,
        "current_page_index": section.pager.first,
    }
    reader.view.set_insertion_point(7)

    def fail_line_lookup(_position):
        raise AssertionError("No section range should mean no line lookup")

    reader.view.get_containing_line = fail_line_lookup

    reader.go_to_first_of_section()

    assert reader.view.get_insertion_point() == 7


def test_section_navigation_stops_cleanly_at_the_end(reader):
    section = make_section("Last", 0, 10)
    reader._EBookReader__state = {"active_section": section}

    assert reader.navigate(to="next", unit="section") is False
    assert reader.active_section is section


def test_section_navigation_handles_duplicate_single_page_titles(reader):
    root = make_section("Document", 0, 30)
    first = make_section("Repeated", 0, 10)
    second = make_section("Repeated", 20, 30)
    root.append(first)
    root.append(second)
    reader.document = SimpleNamespace(
        has_toc_tree=lambda: False,
        is_single_page_document=lambda: True,
    )
    reader._EBookReader__state = {
        "active_section": first,
        "current_page_index": 0,
    }
    reader.view.get_containing_line = lambda _position: (20, 30)

    assert reader.navigate(to="next", unit="section") is True
    assert reader.active_section is second
    assert reader.view.get_insertion_point() == 20


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
    assert record.last_position == reader.view_to_storage_position(test_pos, test_page)
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
    assert record.last_position == reader.view_to_storage_position(test_pos, test_page)
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


def test_fallback_uri_does_not_override_saved_position(reader, tmp_path):
    path = tmp_path / "book.txt"
    path.write_text("0123456789abcdef", encoding="utf-8")
    uri = DocumentUri.from_filename(path)
    uri.fallback_uri = DocumentUri.from_filename(path)

    reader.load(uri)
    reader.go_to_page(0, 7)
    reader.save_current_position()
    reader.unload()

    reader.load(uri)

    assert reader.view.get_insertion_point() == 7
    reader.unload()


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
    assert record.last_position == reader.view_to_storage_position(test_pos, test_page)
    assert record.uri == original_uri
