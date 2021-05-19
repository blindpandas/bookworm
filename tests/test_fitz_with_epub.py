import pytest
from bookworm.document_formats import FitzEPUBDocument

def test_epub_metadata(asset):
    epub = FitzEPUBDocument(asset("The Diary of a Nobody.epub"))
    assert epub._ebook is None
    epub.read()
    assert epub.metadata.title == "The Diary of a Nobody"
    assert epub.metadata.author == "George Grossmith"
    