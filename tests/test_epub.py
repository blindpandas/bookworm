from pathlib import Path

from ebooklib import epub
import pytest

from bookworm.document.uri import DocumentUri
from bookworm.document.formats.epub import EpubDocument

def temp_book(title: str = 'Sample book') -> epub.EpubBook:
    book = epub.EpubBook()
    book.set_title("test book")
    book.set_language('en')
    c1 = epub.EpubHtml(title="Intro", file_name="chap_01.xhtml", lang="en")
    c1.content = (
        "<h1>This is a test</h1>"
    )
    book.add_item(c1)
    book.toc = (
        epub.Link("chap_01.xhtml", "Introduction", "intro"),
        (epub.Section("Simple book"), (c1,)),
    )

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", c1]
    return book


def test_chapter_order_is_unchanged_with_roman_numbers(asset):
    doc = EpubDocument(DocumentUri.from_filename(asset('roman.epub')))
    doc.read()
    spine = [x[0] for x in doc.epub.spine]
    items = [x.file_name.split('/')[-1] for x in doc.epub_html_items]
    assert spine == items

def test_modified_epub_modifies_cache(asset):
    book = temp_book()
    epub.write_epub(asset("test.epub"), book, {})
    doc = EpubDocument(DocumentUri.from_filename(asset('test.epub')))
    doc.read()
    content = doc.html_content

    # Let's now add a second chapter, and see whether the document read modifies its cache
    c2 = epub.EpubHtml(title="Second chapter", file_name="chap_02.xhtml", lang="en")
    c2.content = (
        "<h1>This is another test</h1>"
    )
    book.add_item(c2)
    book.spine.append(c2)
    epub.write_epub(asset("test.epub"), book, {})

    # read the book once more, and verify that the content is different
    doc = EpubDocument(DocumentUri.from_filename(asset('test.epub')))
    doc.read()
    new_content = doc.html_content
    Path(asset("test.epub")).unlink()
    assert content != new_content
