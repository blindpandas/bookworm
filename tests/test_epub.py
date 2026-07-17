import os
from pathlib import Path
from unittest.mock import Mock

from diskcache import Cache
from ebooklib import epub

from bookworm.document import cache_utils
from bookworm.document.formats.epub import EpubDocument
from bookworm.document.uri import DocumentUri


def temp_book(title: str = "Sample book") -> epub.EpubBook:
    book = epub.EpubBook()
    book.set_title("test book")
    book.set_language("en")
    c1 = epub.EpubHtml(title="Intro", file_name="chap_01.xhtml", lang="en")
    c1.content = "<h1>This is a test</h1>"
    book.add_item(c1)
    book.toc = (
        epub.Link("chap_01.xhtml", "Introduction", "intro"),
        (epub.Section("Simple book"), (c1,)),
    )

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", c1]
    return book


def epub_chapter(file_name: str, content: str) -> epub.EpubHtml:
    chapter = epub.EpubHtml(title=file_name, file_name=file_name, lang="en")
    chapter.content = content
    return chapter


def test_chapter_order_is_unchanged_with_roman_numbers(asset):
    doc = EpubDocument(DocumentUri.from_filename(asset("roman.epub")))
    doc.read()
    spine = [x[0] for x in doc.epub.spine]
    items = [x.file_name.split("/")[-1] for x in doc.epub_html_items]
    assert spine == items


def test_modified_epub_modifies_cache(asset):
    book = temp_book()
    epub.write_epub(asset("test.epub"), book, {})
    doc = EpubDocument(DocumentUri.from_filename(asset("test.epub")))
    doc.read()
    content = doc.html_content

    # Let's now add a second chapter, and see whether the document read modifies its cache
    c2 = epub.EpubHtml(title="Second chapter", file_name="chap_02.xhtml", lang="en")
    c2.content = "<h1>This is another test</h1>"
    book.add_item(c2)
    book.spine.append(c2)
    epub.write_epub(asset("test.epub"), book, {})

    # read the book once more, and verify that the content is different
    doc = EpubDocument(DocumentUri.from_filename(asset("test.epub")))
    doc.read()
    new_content = doc.html_content
    Path(asset("test.epub")).unlink()
    assert content != new_content


def test_internal_link_resolution_prefers_exact_href_over_suffix_match(tmp_path):
    book = epub.EpubBook()
    book.set_title("suffix match")
    book.set_language("en")
    wrong_target = epub_chapter(
        "otherchap.xhtml",
        '<h1 id="same">Wrong target</h1><p>Other body</p>',
    )
    link_chapter = epub_chapter(
        "link.xhtml",
        '<p><a href="chap.xhtml#same">Go exact target</a></p>',
    )
    right_target = epub_chapter(
        "chap.xhtml",
        '<h1 id="same">Right target</h1><p>Right body</p>',
    )
    for item in (wrong_target, link_chapter, right_target):
        book.add_item(item)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.toc = (
        epub.Link("link.xhtml", "Link", "link"),
        epub.Link("chap.xhtml#same", "Right", "right"),
    )
    book.spine = ["nav", wrong_target, link_chapter, right_target]
    epub_path = tmp_path / "suffix_match.epub"
    epub.write_epub(epub_path, book, {})
    document = EpubDocument(DocumentUri.from_filename(epub_path))
    document.read()
    text = document.get_content()
    link_range = next(
        text_range
        for text_range, href in document.structure.link_targets.items()
        if href == "chap.xhtml#same" and text[text_range[0] : text_range[1]] == "Go exact target"
    )

    target = document.resolve_link(link_range)
    start, stop = target.position

    assert text[start:stop].strip() == "Right target"


def test_legacy_content_uses_disk_cache(asset, tmp_path, monkeypatch):
    monkeypatch.setattr(EpubDocument, "_get_cache_directory", lambda _: tmp_path / "cache")
    uri = DocumentUri.from_filename(asset("The Diary of a Nobody.epub"))
    first_document = EpubDocument(uri)
    first_document.read()
    legacy_content = first_document.get_legacy_content()

    second_document = EpubDocument(uri)
    second_document.read()
    monkeypatch.setattr(
        EpubDocument,
        "_parse_html_content",
        Mock(side_effect=AssertionError("legacy content should be loaded from disk cache")),
    )

    assert second_document.get_legacy_content() == legacy_content


def test_legacy_cache_uses_the_html_that_was_parsed(asset, tmp_path, monkeypatch):
    monkeypatch.setattr(EpubDocument, "_get_cache_directory", lambda _: tmp_path / "cache")
    epub_path = tmp_path / "book.epub"
    epub_path.write_bytes(Path(asset("epub30-spec.epub")).read_bytes())
    original_mtime = epub_path.stat().st_mtime
    uri = DocumentUri.from_filename(epub_path)
    original_document = EpubDocument(uri)
    original_document.read()

    epub_path.write_bytes(Path(asset("roman.epub")).read_bytes())
    os.utime(epub_path, (original_mtime + 2, original_mtime + 2))
    original_legacy_content = original_document.get_legacy_content()
    replacement_document = EpubDocument(uri)
    replacement_document.read()

    assert replacement_document.get_legacy_content() != original_legacy_content


def test_epub_cache_failures_fall_back_to_in_memory_parsing(asset, tmp_path, monkeypatch):
    cache_directory = tmp_path / "cache"
    monkeypatch.setattr(EpubDocument, "_get_cache_directory", lambda _: cache_directory)
    uri = DocumentUri.from_filename(asset("The Diary of a Nobody.epub"))
    original_document = EpubDocument(uri)
    original_document.read()
    expected_content = original_document.get_content()
    expected_legacy_content = original_document.get_legacy_content()
    with Cache(cache_directory) as cache:
        cache.set(original_document._legacy_content_cache_key, b"\xff")
    monkeypatch.setattr(
        cache_utils,
        "is_document_modified",
        Mock(side_effect=OSError("cache validation failed")),
    )

    replacement_document = EpubDocument(uri)
    replacement_document.read()

    assert replacement_document.get_content() == expected_content
    assert replacement_document.get_legacy_content() == expected_legacy_content
