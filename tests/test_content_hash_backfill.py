import shutil
from pathlib import Path

from alembic import command
from alembic.config import Config
from pptx import Presentation
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import close_all_sessions
from sqlalchemy.pool import NullPool

from bookworm.annotation import NoteTaker
from bookworm.database import init_database
from bookworm.database.models import (
    Book,
    DocumentPositionInfo,
    Note,
    PinnedDocument,
    RecentDocument,
)
from bookworm.document import BaseDocument, BasePage, BookMetadata, Pager, Section, create_document
from bookworm.document.uri import DocumentUri
from bookworm.gui.book_viewer import recents_manager


def _make_alembic_config(db_url):
    cfg = Config(Path("alembic.ini"))
    cfg.attributes["configure_logger"] = False
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _make_textless_presentation(filename):
    presentation = Presentation()
    presentation.slides.add_slide(presentation.slide_layouts[6])
    presentation.save(filename)


class _SyntheticPaginatedPage(BasePage):
    def get_text(self):
        return self.document.page_texts[self.index]


class _SyntheticPaginatedDocument(BaseDocument):
    __internal__ = True
    format = "test_paginated_hash"
    extensions = ()

    def __init__(self, uri, page_texts, *, title="Paged Document"):
        super().__init__(uri)
        self.page_texts = tuple(page_texts)
        self._metadata = BookMetadata(title=title, author="")

    def __len__(self):
        return len(self.page_texts)

    def read(self):
        super().read()

    def get_page(self, index):
        return _SyntheticPaginatedPage(self, index)

    @property
    def toc_tree(self):
        return Section(title=self.metadata.title, pager=Pager(first=0, last=len(self) - 1))

    @property
    def metadata(self):
        return self._metadata


def _make_synthetic_paginated_document(path, *page_texts, title="Paged Document"):
    document = _SyntheticPaginatedDocument(
        DocumentUri(
            format=_SyntheticPaginatedDocument.format,
            path=path,
            openner_args={},
        ),
        page_texts,
        title=title,
    )
    document.read()
    return document


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


def test_content_hash_migration_only_adds_schema(asset, tmp_path):
    db_path = tmp_path / "migration.db"
    db_url = f"sqlite:///{db_path}"
    document_uri = DocumentUri.from_filename(asset("test.md")).to_uri_string()

    command.upgrade(_make_alembic_config(db_url), "52e39c4f7494")

    seed_engine = create_engine(db_url, poolclass=NullPool)
    with seed_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO book (title, uri) VALUES (:title, :uri)"),
            {"title": "book", "uri": document_uri},
        )
        conn.execute(
            text(
                "INSERT INTO document_position_info (title, uri, last_page, last_position) "
                "VALUES (:title, :uri, :last_page, :last_position)"
            ),
            {"title": "position", "uri": document_uri, "last_page": 0, "last_position": 0},
        )
        conn.execute(
            text("INSERT INTO recent_document (title, uri) VALUES (:title, :uri)"),
            {"title": "recent", "uri": document_uri},
        )
        conn.execute(
            text(
                "INSERT INTO pinned_document (title, uri, is_pinned, pinning_order) "
                "VALUES (:title, :uri, :is_pinned, :pinning_order)"
            ),
            {"title": "pinned", "uri": document_uri, "is_pinned": True, "pinning_order": 0},
        )
    seed_engine.dispose()

    migrated_engine = init_database(url=db_url, poolclass=NullPool)
    try:
        with migrated_engine.connect() as conn:
            revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            assert revision == "707543f03b6d"
            for table_name in (
                "book",
                "document_position_info",
                "recent_document",
                "pinned_document",
            ):
                content_hashes = conn.execute(
                    text(f"SELECT content_hash FROM {table_name}")
                ).scalars().all()
                assert content_hashes == [None]
    finally:
        close_all_sessions()
        migrated_engine.dispose()


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


def test_paginated_content_hash_preserves_page_boundaries():
    first_document = _make_synthetic_paginated_document("first", "alpha", "beta")
    second_document = _make_synthetic_paginated_document("second", "alphab", "eta")
    try:
        assert first_document.get_content_hash() != second_document.get_content_hash()
    finally:
        first_document.close()
        second_document.close()


def test_paginated_documents_with_same_flattened_text_do_not_merge(reader):
    first_document = _make_synthetic_paginated_document(
        "first", "alpha", "beta", title="Paged Document"
    )
    second_document = _make_synthetic_paginated_document(
        "second", "alphab", "eta", title="Paged Document"
    )

    reader.set_document(first_document)
    reader.go_to_page(1, 3)
    reader.save_current_position()
    reader.unload()

    reader.set_document(second_document)

    assert Book.query.count() == 2
    assert DocumentPositionInfo.query.count() == 2
    assert reader.stored_document_info.get_last_position() == (0, 0)
    reader.unload()


def test_textless_documents_do_not_merge_by_content_hash(reader, tmp_path):
    first_path = tmp_path / "first.pptx"
    second_path = tmp_path / "second.pptx"
    _make_textless_presentation(first_path)
    _make_textless_presentation(second_path)

    first_uri = DocumentUri.from_filename(first_path)
    second_uri = DocumentUri.from_filename(second_path)

    first_doc = create_document(first_uri)
    try:
        assert first_doc.get_content_hash() is None
    finally:
        first_doc.close()

    reader.load(first_uri)
    reader.unload()
    reader.load(second_uri)

    assert Book.query.count() == 2
    assert DocumentPositionInfo.query.count() == 2
    assert {record.uri for record in Book.query.all()} == {first_uri, second_uri}
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
def test_textless_recent_documents_do_not_merge_by_content_hash(tmp_path):
    first_path = tmp_path / "first.pptx"
    second_path = tmp_path / "second.pptx"
    _make_textless_presentation(first_path)
    _make_textless_presentation(second_path)

    first_doc = create_document(DocumentUri.from_filename(first_path))
    second_doc = create_document(DocumentUri.from_filename(second_path))
    try:
        recents_manager.add_to_recents(first_doc)
        recents_manager.add_to_recents(second_doc)
    finally:
        first_doc.close()
        second_doc.close()

    assert RecentDocument.query.count() == 2


def test_loading_existing_uri_uses_stored_hash_without_recomputing(
    reader, asset, monkeypatch
):
    uri = DocumentUri.from_filename(asset("roman.epub"))
    document = create_document(uri)
    content_hash = document.get_content_hash()

    Book.get_or_create(
        title=document.metadata.title,
        uri=uri,
        content_hash=content_hash,
    )
    DocumentPositionInfo.get_or_create(
        title=document.metadata.title,
        uri=uri,
        content_hash=content_hash,
    )

    def fail_get_content_hash():
        raise AssertionError(
            "reader should reuse the stored content hash for URI matches"
        )

    monkeypatch.setattr(document, "get_content_hash", fail_get_content_hash)

    reader.set_document(document)

    assert reader.current_book_record.content_hash == content_hash
    assert reader.stored_document_info.content_hash == content_hash
    reader.unload()


@pytest.mark.usefixtures("engine")
def test_recent_documents_with_existing_uri_use_stored_hash_without_recomputing(
    asset, monkeypatch
):
    uri = DocumentUri.from_filename(asset("roman.epub"))
    document = create_document(uri)
    content_hash = document.get_content_hash()

    existing_recent = RecentDocument.get_or_create(
        title=document.metadata.title,
        uri=uri,
        content_hash=content_hash,
    )

    def fail_get_content_hash():
        raise AssertionError(
            "recents should reuse the stored content hash for URI matches"
        )

    monkeypatch.setattr(document, "get_content_hash", fail_get_content_hash)

    try:
        recents_manager.add_to_recents(document)
    finally:
        document.close()

    assert RecentDocument.query.one().id == existing_recent.id


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
