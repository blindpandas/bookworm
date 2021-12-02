import pytest
from bookworm.document.uri import DocumentUri
from bookworm.document.formats import EpubDocument


def test_epub_metadata(asset):
    uri = DocumentUri.from_filename(asset("The Diary of a Nobody.epub"))
    epub = EpubDocument(uri)
    epub.read()
    assert epub.metadata.title == "The Diary of a Nobody"
    assert epub.metadata.author == "George Grossmith"
