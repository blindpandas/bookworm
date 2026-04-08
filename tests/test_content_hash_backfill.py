import shutil
from pathlib import Path

import pytest

from bookworm.annotation import NoteTaker
from bookworm.database.models import (
    Book,
    DocumentPositionInfo,
    Note,
    PinnedDocument,
    RecentDocument,
)
from bookworm.document import create_document
from bookworm.document.uri import DocumentUri
from bookworm.gui.book_viewer import recents_manager


def test_loading_existing_records_backfills_hashes_and_preserves_annotations(
    asset, reader, tmp_path
):
    original_uri = DocumentUri.from_filename(asset("roman.epub"))
    original_doc = create_document(original_uri)
    content_hash = original_doc.get_content_hash()

    existing_book = Book.get_or_create(title=original_doc.metadata.title, uri=original_uri)
    existing_doc_info = DocumentPositionInfo.get_or_create(
        title=original_doc.metadata.title,
        uri=original_uri,
    )
    Note.session().add(
        Note(
            title="test",
            content="test note",
            page_number=0,
            position=0,
            section_title="test section",
            section_identifier="test-section",
            book_id=existing_book.id,
        )
    )
    Note.session().commit()

    reader.load(original_uri)

    updated_book = Book.query.one()
    updated_doc_info = DocumentPositionInfo.query.one()
    assert updated_book.id == existing_book.id
    assert updated_doc_info.id == existing_doc_info.id
    assert updated_book.content_hash == content_hash
    assert updated_doc_info.content_hash == content_hash
    reader.unload()

    moved_path = shutil.copy(Path(original_uri.path), tmp_path / "roman.epub")
    moved_uri = DocumentUri.from_filename(moved_path)
    reader.load(moved_uri)

    assert Book.query.count() == 1
    assert DocumentPositionInfo.query.count() == 1
    assert Book.query.one().uri == moved_uri
    assert DocumentPositionInfo.query.one().uri == moved_uri
    assert NoteTaker(reader).get_for_page(0).count() == 1


def test_filename_derived_titles_follow_moved_paths(reader, tmp_path):
    first_path = tmp_path / "first.txt"
    second_path = tmp_path / "second.txt"
    first_path.write_text("same text", encoding="utf-8")
    second_path.write_text("same text", encoding="utf-8")

    first_uri = DocumentUri.from_filename(first_path)
    second_uri = DocumentUri.from_filename(second_path)

    reader.load(first_uri)
    first_book = Book.query.one()
    first_position_info = DocumentPositionInfo.query.one()
    reader.view.set_insertion_point(4)
    reader.unload()

    reader.load(second_uri)

    assert Book.query.count() == 1
    assert DocumentPositionInfo.query.count() == 1
    assert Book.query.one().id == first_book.id
    assert DocumentPositionInfo.query.one().id == first_position_info.id
    assert Book.query.one().uri == second_uri
    assert DocumentPositionInfo.query.one().uri == second_uri
    assert reader.stored_document_info.get_last_position() == (0, 4)
    reader.unload()


def test_duplicate_hash_matches_are_merged_into_active_document(reader, tmp_path):
    first_path = tmp_path / "first.txt"
    second_path = tmp_path / "second.txt"
    first_path.write_text("same text", encoding="utf-8")
    second_path.write_text("same text", encoding="utf-8")

    first_uri = DocumentUri.from_filename(first_path)
    second_uri = DocumentUri.from_filename(second_path)
    content_hash = create_document(first_uri).get_content_hash()

    first_book = Book.get_or_create(
        title="first",
        uri=first_uri,
        content_hash=content_hash,
    )
    second_book = Book.get_or_create(
        title="second",
        uri=second_uri,
        content_hash=content_hash,
    )
    first_position_info = DocumentPositionInfo.get_or_create(
        title="first",
        uri=first_uri,
        content_hash=content_hash,
    )
    first_position_info.save_position(0, 7)
    DocumentPositionInfo.get_or_create(
        title="second",
        uri=second_uri,
        content_hash=content_hash,
    )
    Note.session().add(
        Note(
            title="test",
            content="test note",
            page_number=0,
            position=0,
            section_title="test section",
            section_identifier="test-section",
            book_id=first_book.id,
        )
    )
    Note.session().commit()

    reader.load(second_uri)

    assert Book.query.count() == 1
    assert Book.query.one().id == second_book.id
    assert Note.query.one().book_id == second_book.id
    assert NoteTaker(reader).get_for_page(0).count() == 1
    assert DocumentPositionInfo.query.count() == 1
    assert DocumentPositionInfo.query.one().uri == second_uri
    assert reader.stored_document_info.get_last_position() == (0, 7)
    reader.unload()


@pytest.mark.usefixtures("engine")
def test_recent_documents_follow_path_changes_after_lazy_hash_backfill(
    asset, tmp_path
):
    original_uri = DocumentUri.from_filename(asset("roman.epub"))
    original_doc = create_document(original_uri)

    existing_recent = RecentDocument.get_or_create(
        title=original_doc.metadata.title,
        uri=original_uri,
    )
    assert existing_recent.content_hash is None

    recents_manager.add_to_recents(original_doc)

    updated_recent = RecentDocument.query.one()
    assert updated_recent.id == existing_recent.id
    assert updated_recent.content_hash == original_doc.get_content_hash()

    moved_path = shutil.copy(Path(original_uri.path), tmp_path / "roman.epub")
    moved_doc = create_document(DocumentUri.from_filename(moved_path))
    recents_manager.add_to_recents(moved_doc)

    assert RecentDocument.query.count() == 1
    recent = RecentDocument.query.one()
    assert recent.id == existing_recent.id
    assert recent.uri == moved_doc.uri


@pytest.mark.usefixtures("engine")
def test_pinned_documents_follow_path_changes_after_lazy_hash_backfill(
    asset, tmp_path
):
    original_uri = DocumentUri.from_filename(asset("roman.epub"))
    original_doc = create_document(original_uri)

    existing_pinned = PinnedDocument.get_or_create(
        title=original_doc.metadata.title,
        uri=original_uri,
    )
    existing_pinned.pin()
    assert existing_pinned.content_hash is None

    assert recents_manager.is_pinned(original_doc) is True

    updated_pinned = PinnedDocument.query.one()
    assert updated_pinned.id == existing_pinned.id
    assert updated_pinned.content_hash == original_doc.get_content_hash()

    moved_path = shutil.copy(Path(original_uri.path), tmp_path / "roman.epub")
    moved_doc = create_document(DocumentUri.from_filename(moved_path))

    assert recents_manager.is_pinned(moved_doc) is True
    assert PinnedDocument.query.count() == 1
    pinned = PinnedDocument.query.one()
    assert pinned.id == existing_pinned.id
    assert pinned.uri == moved_doc.uri
