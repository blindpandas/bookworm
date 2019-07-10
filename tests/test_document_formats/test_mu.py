import pytest
from bookworm.document_formats import mu


def test_fitz_document(ebooks_dir):
    document = mu.FitzDocument(
        ebooks_dir / "alices_adventures_in_wonderland_carroll_lewis.epub"
    )
    assert document._ebook is None
    document.read()
    assert document._ebook is not None
    assert document.metadata.title
    document.close()
