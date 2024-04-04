import pytest

from bookworm.document.uri import DocumentUri
from bookworm.document.formats.epub import EpubDocument


def test_chapter_order_is_unchanged_with_roman_numbers(asset):
    epub = EpubDocument(DocumentUri.from_filename(asset('roman.epub')))
    epub.read()
    spine = [x[0] for x in epub.epub.spine]
    items = [x.file_name.split('/')[-1] for x in epub.epub_html_items]
    print(items)
    print(spine)
    assert spine == items
