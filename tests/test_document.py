from pathlib import Path

import pytest

from bookworm.database import Book, DocumentPositionInfo
from bookworm.document import create_document
from bookworm.document.uri import DocumentUri


def test_epub_metadata(asset):
    uri = DocumentUri.from_filename(asset("The Diary of a Nobody.epub"))
    epub = create_document(uri)
    assert epub.metadata.title == "The Diary of a Nobody"
    assert epub.metadata.author == "George Grossmith"


def test_epub_document_section_at_text_position(asset):
    uri = DocumentUri.from_filename(asset("epub30-spec.epub"))
    epub = create_document(uri)
    position_to_section_title = {
        247743: "1.1. Purpose and Scope",
        370161: "3.1.1. HTML5",
        127838: "4.3.2. Metadata meta Properties",
        242323: "B.4.1.2. Description",
        17556: "Terminology",
        34564: "2.6. Rendering and CSS",
        349355: "Acknowledgements and Contributors",
        363566: "EPUB 3 Changes from EPUB 2.0.1",
        371108: "3.1.5. Content Switching",
        135534: "4.3.2. Metadata meta Properties",
        130440: "4.3.2. Metadata meta Properties",
        60425: "2.2. Reading System Conformance",
        49786: "4.6. Scripting",
        278229: "3.5.2. Media Overlays Metadata Vocabulary",
        63656: "3.4.1. The package Element",
        380720: "4.1.4. Filesystem Container",
        173840: "2.1.3.1.3. Vocabulary Association",
        25363: "1.2. Roadmap",
        114545: "4.2.2. Default Vocabulary",
        9227: "EPUB 3 Specifications - Table of Contents",
    }
    for text_position, section_title in position_to_section_title.items():
        section = epub.get_section_at_position(text_position)
        assert section.title == section_title


def test_opening_reader_creates_book_and_document_info(asset, reader):
    uri = DocumentUri.from_filename(asset("The Diary of a Nobody.epub"))
    doc = create_document(uri)
    content_hash = doc.get_content_hash()
    reader.set_document(doc)
    assert Book.query.count() == 1
    assert DocumentPositionInfo.query.count() == 1


def test_opening_existing_document_falls_bac_kto_same_entry(reader, asset):
    uri = DocumentUri.from_filename(asset("The Diary of a Nobody.epub"))
    doc = create_document(uri)
    content_hash = doc.get_content_hash()
    doc_entry = DocumentPositionInfo.get_or_create(
        title=doc.metadata.title, uri=uri, content_hash=content_hash
    )
    book_entry = Book.get_or_create(
        title=doc.metadata.title, uri=uri, content_hash=content_hash
    )
    reader.set_document(doc)
    assert DocumentPositionInfo.query.count() == 1
    assert Book.query.count() == 1

def test_document_with_different_format_and_name_creates_new_entry(asset, reader):
    path = Path(asset("test.md"))
    uri = DocumentUri.from_filename(path)
    reader.load(uri)
    reader.unload()
    new_path = Path(path.parent, "test.txt")
    new_path.write_text(path.read_text())
    new_uri = DocumentUri.from_filename(new_path)
    reader.load(new_uri)
    reader.unload()
    new_path.unlink(missing_ok=True)
    assert Book.query.count() == 2

