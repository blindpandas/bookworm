import pytest
from bookworm.document.uri import DocumentUri
from bookworm.document import create_document


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
        127838: "4.3.2. Metadata ",
        242323: "B.4.1.2. Description",
        17556: "Terminology",
        34564: "2.6. Rendering and CSS",
        349355: "Acknowledgements and Contributors",
        363566: "EPUB 3 Changes from EPUB 2.0.1",
        371108: "3.1.5. Content Switching",
        135534: "4.3.2. Metadata ",
        130440: "4.3.2. Metadata ",
        60425: "2.2. Reading System Conformance",
        49786: "4.6. Scripting",
        278229: "3.5.2. Media Overlays Metadata Vocabulary",
        63656: "3.4.1. The ",
        380720: "4.1.4. Filesystem Container",
        173840: "2.1.3.1.3. Vocabulary Association",
        25363: "1.2. Roadmap",
        114545: "4.2.2. Default Vocabulary",
        9227: "EPUB 3 Specifications - Table of Contents",
    }
    for (text_position, section_title) in position_to_section_title.items():
        section = epub.get_section_at_position(text_position)
        assert section.title == section_title
