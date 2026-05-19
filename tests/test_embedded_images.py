import base64
import os
import zipfile
from functools import cached_property
from io import BytesIO
from types import SimpleNamespace

import pytest
from ebooklib import epub
from PIL import Image

from bookworm.document import (
    SINGLE_PAGE_DOCUMENT_PAGER,
    BookMetadata,
    DocumentCapability,
    DocumentIOError,
    LinkTarget,
    Section,
    SinglePageDocument,
)
from bookworm.document.formats.epub import EpubDocument
from bookworm.document.formats.html import FileSystemHtmlDocument
from bookworm.document.formats.odf import OdfPresentation
from bookworm.document.uri import DocumentUri
from bookworm.gui.book_viewer import _get_structural_navigation_speech
from bookworm.gui.book_viewer.render_view import EmbeddedImageDialog
from bookworm.image_io import ImageIO
from bookworm.structured_text import (
    TEXT_OBJECT_REPLACEMENT_CHAR,
    ImageElementInfo,
    SemanticElementType,
    TextPositionMap,
    TextRange,
)
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser


def make_png_bytes(size=(3, 2), color=(255, 0, 0)):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def make_transparent_png_bytes():
    buf = BytesIO()
    image = Image.new("RGBA", (2, 1), (255, 0, 0, 255))
    image.putpixel((1, 0), (0, 255, 0, 0))
    image.save(buf, format="PNG")
    return buf.getvalue()


def make_palette_png_bytes():
    image = Image.new("P", (2, 1))
    image.putpalette([255, 0, 0, 0, 255, 0] + [0, 0, 0] * 254)
    image.putdata([0, 1])
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def make_epub_image_item(
    uid,
    file_name,
    *,
    size=(6, 7),
    media_type="image/png",
    content=None,
):
    return epub.EpubItem(
        uid=uid,
        file_name=file_name,
        media_type=media_type,
        content=make_png_bytes(size=size) if content is None else content,
    )


def make_epub_document(tmp_path, chapter_content, *items):
    book = epub.EpubBook()
    book.set_title("Image book")
    book.set_language("en")
    chapter = epub.EpubHtml(title="Intro", file_name="chapters/ch1.xhtml", lang="en")
    chapter.content = chapter_content
    book.add_item(chapter)
    for item in items:
        book.add_item(item)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.toc = (epub.Link("chapters/ch1.xhtml", "Intro", "intro"),)
    book.spine = ["nav", chapter]
    epub_path = tmp_path / "image_book.epub"
    epub.write_epub(epub_path, book, {})
    document = EpubDocument(DocumentUri.from_filename(epub_path))
    document.read()
    return document


class SyntheticImageDocument(SinglePageDocument):
    __internal__ = True
    format = "synthetic_image_document"
    extensions = ()
    capabilities = (
        DocumentCapability.SINGLE_PAGE
        | DocumentCapability.STRUCTURED_NAVIGATION
        | DocumentCapability.TOC_TREE
        | DocumentCapability.LINKS
    )

    def __init__(
        self,
        text,
        semantic_structure,
        *,
        image_infos=(),
        images=(),
        image_error=None,
        link_target=None,
    ):
        super().__init__(DocumentUri(self.format, "", {}))
        self.text = text
        self.document_semantic_structure = semantic_structure
        self.image_infos = image_infos
        self.images = images
        self.image_error = image_error
        self.link_target = link_target

    def read(self):
        super().read()

    def get_content(self):
        return self.text

    @cached_property
    def toc_tree(self):
        return Section(
            title="Synthetic",
            pager=SINGLE_PAGE_DOCUMENT_PAGER,
            text_range=TextRange(0, len(self.text)),
        )

    @cached_property
    def metadata(self):
        return BookMetadata(title="Synthetic", author="")

    def get_document_semantic_structure(self):
        return self.document_semantic_structure

    def get_document_style_info(self):
        return {}

    def get_document_table_markup(self, table_index):
        raise NotImplementedError

    def get_document_embedded_image_info(self, image_index):
        return self.image_infos[image_index]

    def get_document_embedded_image(self, image_index):
        if self.image_error:
            raise self.image_error
        return self.images[image_index]

    def resolve_link(self, text_range):
        if self.link_target:
            return self.link_target
        raise NotImplementedError


def test_structured_html_parser_collects_image_ranges_and_metadata():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            before <img src="images/alt.png" alt="Alt text"> after
            <img src="images/title.png" title="Title text">
            <figure>
                <img src="images/caption.png">
                <figcaption>Caption text</figcaption>
            </figure>
            <img src="images/fallback.png">
        </body></html>
        """
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == [
        "[Alt text]",
        "[Title text]",
        "[Caption text]",
        "[Image]",
    ]
    assert [parser.get_image_info(idx).label for idx in range(4)] == [
        "Alt text",
        "Title text",
        "Caption text",
        "Image",
    ]
    assert parser.get_image_info(0).suggested_filename == "alt.png"


def test_structured_html_parser_uses_stable_storage_placeholders():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            before <img src="images/alt.png" alt="Alt text"> after
            <img src="images/fallback.png">
        </body></html>
        """
    )

    display_text = parser.get_text()
    storage_text = parser.get_storage_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [display_text[start:stop] for start, stop in ranges] == [
        "[Alt text]",
        "[Image]",
    ]
    assert storage_text.count(TEXT_OBJECT_REPLACEMENT_CHAR) == 2
    for start, stop in ranges:
        storage_range = parser.display_to_storage_range(start, stop)
        assert (
            storage_text[storage_range.start : storage_range.stop] == TEXT_OBJECT_REPLACEMENT_CHAR
        )
        assert parser.storage_to_display_range(
            storage_range.start, storage_range.stop
        ).astuple() == (start, stop)


def test_structured_html_parser_keeps_range_stops_before_following_images():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            before <img src="images/alt.png" alt="Alt text"> after
        </body></html>
        """
    )

    display_text = parser.get_text()
    storage_text = parser.get_storage_text()
    image_start, image_stop = parser.semantic_elements[SemanticElementType.FIGURE][0]

    before_image = parser.display_to_storage_range(0, image_start)
    assert storage_text[before_image.start : before_image.stop] == display_text[:image_start]
    assert TEXT_OBJECT_REPLACEMENT_CHAR not in storage_text[before_image.start : before_image.stop]
    assert parser.storage_to_display_range(before_image.start, before_image.stop).astuple() == (
        0,
        image_start,
    )

    image_and_text = parser.display_to_storage_range(0, image_stop)
    assert storage_text[image_and_text.start : image_and_text.stop].endswith(
        TEXT_OBJECT_REPLACEMENT_CHAR
    )


def test_text_position_map_from_texts_preserves_legacy_image_boundaries():
    legacy_text = "before middle after text\n"
    storage_text = f"before {TEXT_OBJECT_REPLACEMENT_CHAR} middle {TEXT_OBJECT_REPLACEMENT_CHAR} after text\n"
    mapper = TextPositionMap.from_texts(legacy_text, storage_text)

    after_text = legacy_text.index("after")
    second_image = storage_text.index(
        TEXT_OBJECT_REPLACEMENT_CHAR,
        storage_text.index(TEXT_OBJECT_REPLACEMENT_CHAR) + 1,
    )
    after_text_storage = storage_text.index("after")

    assert mapper.display_to_storage_position(after_text, affinity="before") == second_image
    assert mapper.display_to_storage_position(after_text, affinity="after") == after_text_storage
    assert mapper.display_to_storage_range(0, after_text).stop == second_image
    assert mapper.display_to_storage_range(after_text, after_text + len("after")).start == (
        after_text_storage
    )


def test_html_legacy_content_hash_uses_pre_image_navigation_text(tmp_path):
    image_path = tmp_path / "pic.png"
    image_path.write_bytes(make_png_bytes())
    html_path = tmp_path / "book.html"
    html_path.write_text(
        """
        <html>
            <head><title>Book</title></head>
            <body><p>alpha <img src="pic.png" alt="Picture"> omega</p></body>
        </html>
        """,
        encoding="utf-8",
    )
    document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
    document.read()

    try:
        legacy_parser = StructuredHtmlParser.from_string(
            html_path.read_text(encoding="utf-8"),
            include_images=False,
        )
        legacy_text = legacy_parser.get_text()
        assert TEXT_OBJECT_REPLACEMENT_CHAR not in legacy_text
        assert document.get_legacy_content() == legacy_text
        assert document.get_legacy_content_hash() == document._hash_document_text(
            legacy_text
        )
    finally:
        document.close()


def test_structured_html_parser_ignores_symbol_only_image_alt_text():
    parser = StructuredHtmlParser.from_string(
        '<html><body><img src="images/pic.png" alt="{%}"></body></html>'
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == ["[Image]"]
    assert parser.get_image_info(0).label == "Image"


def test_structured_html_parser_uses_title_when_alt_is_not_meaningful():
    parser = StructuredHtmlParser.from_string(
        '<html><body><img src="images/pic.png" alt="{%}" title="Diagram"></body></html>'
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == ["[Diagram]"]
    assert parser.get_image_info(0).label == "Diagram"


def test_structured_html_parser_skips_images_with_empty_alt_text():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <img src="images/decorative.png" alt="">
            <img src="images/content.png" alt="Content">
        </body></html>
        """
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == ["[Content]"]
    assert parser.get_image_info(0).src == "images/content.png"


def test_structured_html_parser_keeps_empty_alt_images_with_title():
    parser = StructuredHtmlParser.from_string(
        '<html><body><img src="images/pic.png" alt="" title="Diagram"></body></html>'
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == ["[Diagram]"]
    assert parser.get_image_info(0).label == "Diagram"


def test_structured_html_parser_keeps_empty_alt_images_with_caption():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <figure>
                <img src="images/pic.png" alt="">
                <figcaption>Diagram caption</figcaption>
            </figure>
        </body></html>
        """
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == ["[Diagram caption]"]
    assert parser.get_image_info(0).label == "Diagram caption"


def test_structured_html_parser_places_image_ranges_after_rendered_prefixes():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <ul>
                <li><img src="images/list.png" alt="List image"> item</li>
            </ul>
            <table>
                <tr>
                    <td><img src="images/table.png" alt="Table image"></td>
                    <td>cell</td>
                </tr>
            </table>
        </body></html>
        """
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == [
        "[List image]",
        "[Table image]",
    ]


def test_structured_html_parser_matches_visible_table_image_when_text_repeats():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <table>
                <tr>
                    <td>[Diagram]</td>
                    <td>
                        <img src="images/hidden.png" alt="Diagram" style="display:none">
                        <img src="images/shown.png" alt="Diagram">
                    </td>
                </tr>
            </table>
        </body></html>
        """
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == ["[Diagram]"]
    assert parser.get_image_info(0).src == "images/shown.png"


def test_structured_html_parser_honors_hidden_attribute_when_filtering_images():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <img src="images/hidden.png" alt="Hidden" hidden>
            <div hidden>
                <img src="images/ancestor-hidden.png" alt="Ancestor hidden">
            </div>
            <img src="images/shown.png" alt="Shown">
        </body></html>
        """
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == ["[Shown]"]
    assert parser.get_image_info(0).src == "images/shown.png"


def test_structured_html_parser_honors_important_when_filtering_hidden_images():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <img src="images/hidden.png" alt="Hidden" style="display: none !important">
            <img src="images/shown.png" alt="Shown">
        </body></html>
        """
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]

    assert [text[start:stop] for start, stop in ranges] == ["[Shown]"]
    assert parser.get_image_info(0).src == "images/shown.png"


def test_structured_html_parser_keeps_figure_ranges_and_image_info_in_lockstep():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <p>[Chart]</p>
            <img src="images/hidden.png" alt="Chart" style="display:none">
            <img src="images/decorative.png" alt="">
            <ul>
                <li><img src="images/list.png" alt="Chart"> item</li>
            </ul>
            <table>
                <tr>
                    <td>[Chart]</td>
                    <td><img src="images/table.png" alt="Chart"></td>
                </tr>
            </table>
        </body></html>
        """
    )

    text = parser.get_text()
    ranges = parser.semantic_elements[SemanticElementType.FIGURE]
    image_infos = [parser.get_image_info(idx) for idx in range(len(ranges))]

    assert [text[start:stop] for start, stop in ranges] == ["[Chart]", "[Chart]"]
    assert [(info.label, info.src) for info in image_infos] == [
        ("Chart", "images/list.png"),
        ("Chart", "images/table.png"),
    ]
    with pytest.raises(IndexError):
        parser.get_image_info(len(ranges))


def test_html_document_resolves_local_embedded_image(tmp_path):
    image_path = tmp_path / "images" / "diagram.png"
    image_path.parent.mkdir()
    image_path.write_bytes(make_png_bytes(size=(4, 5)))
    html_path = tmp_path / "book.html"
    html_path.write_text(
        '<html><head><title>Book</title></head><body><img src="images/diagram.png" alt="Diagram"></body></html>',
        encoding="utf-8",
    )
    document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
    document.read()

    image_info = document.get_document_embedded_image_info(0)
    image = document.get_document_embedded_image(0)

    assert image_info.label == "Diagram"
    assert image_info.suggested_filename == "diagram.png"
    assert image.size == (4, 5)


def test_html_document_resolves_local_embedded_image_against_base_href(tmp_path):
    image_path = tmp_path / "images" / "diagram.png"
    image_path.parent.mkdir()
    image_path.write_bytes(make_png_bytes(size=(4, 5)))
    html_path = tmp_path / "book.html"
    html_path.write_text(
        '<html><head><title>Book</title><base href="images/"></head><body><img src="diagram.png" alt="Diagram"></body></html>',
        encoding="utf-8",
    )
    document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
    document.read()

    assert document.get_document_embedded_image(0).size == (4, 5)


def test_html_document_preserves_alpha_for_local_embedded_image(tmp_path):
    image_path = tmp_path / "transparent.png"
    image_path.write_bytes(make_transparent_png_bytes())
    html_path = tmp_path / "book.html"
    html_path.write_text(
        '<html><head><title>Book</title></head><body><img src="transparent.png" alt="Transparent"></body></html>',
        encoding="utf-8",
    )
    document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
    document.read()

    image = document.get_document_embedded_image(0)

    assert image.mode == "RGBA"
    assert image.to_pil().getpixel((1, 0)) == (0, 255, 0, 0)


def test_html_document_resolves_file_uri_embedded_image(tmp_path):
    image_path = tmp_path / "diagram.png"
    image_path.write_bytes(make_png_bytes(size=(4, 5)))
    html_path = tmp_path / "book.html"
    html_path.write_text(
        f'<html><head><title>Book</title></head><body><img src="{image_path.as_uri()}" alt="Diagram"></body></html>',
        encoding="utf-8",
    )
    document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
    document.read()

    assert document.get_document_embedded_image(0).size == (4, 5)


@pytest.mark.skipif(os.name != "nt", reason="UNC file URI resolution is Windows-specific")
def test_html_document_preserves_unc_host_in_file_uri():
    document = FileSystemHtmlDocument.__new__(FileSystemHtmlDocument)

    image_path = document._resolve_image_path("file://server/share/pic.png")

    assert str(image_path) == r"\\server\share\pic.png"


def test_html_document_resolves_drive_style_embedded_image(tmp_path):
    image_path = tmp_path / "diagram.png"
    if not image_path.drive:
        pytest.skip("Drive-style image paths are only meaningful on Windows")
    image_path.write_bytes(make_png_bytes(size=(4, 5)))
    html_path = tmp_path / "book.html"
    html_path.write_text(
        f'<html><head><title>Book</title></head><body><img src="{image_path.as_posix()}" alt="Diagram"></body></html>',
        encoding="utf-8",
    )
    document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
    document.read()

    assert document.get_document_embedded_image(0).size == (4, 5)


def test_html_document_rejects_protocol_relative_embedded_image(tmp_path):
    html_path = tmp_path / "book.html"
    html_path.write_text(
        '<html><head><title>Book</title></head><body><img src="//cdn.example.com/diagram.png" alt="Diagram"></body></html>',
        encoding="utf-8",
    )
    document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
    document.read()

    with pytest.raises(DocumentIOError, match="Remote images"):
        document.get_document_embedded_image(0)


def test_epub_document_resolves_package_embedded_image(tmp_path):
    document = make_epub_document(
        tmp_path,
        '<html><body><h1>Intro</h1><p><img src="../images/pic.png" alt="Picture"></p></body></html>',
        make_epub_image_item("pic", "images/pic.png", size=(6, 7)),
    )

    image_info = document.get_document_embedded_image_info(0)
    image = document.get_document_embedded_image(0)

    assert image_info.label == "Picture"
    assert image.size == (6, 7)


def test_epub_document_resolves_domain_like_package_relative_image(tmp_path):
    document = make_epub_document(
        tmp_path,
        '<html><body><h1>Intro</h1><p><img src="foo.com/pic.png" alt="Picture"></p></body></html>',
        make_epub_image_item("pic", "chapters/foo.com/pic.png", size=(5, 6)),
    )

    assert document.get_document_embedded_image(0).size == (5, 6)


def test_epub_document_strips_query_and_fragment_before_unquoting_image_href(
    tmp_path,
):
    document = make_epub_document(
        tmp_path,
        '<html><body><h1>Intro</h1><p><img src="../images/foo%23bar.png?cache=1#figure" alt="Picture"></p></body></html>',
        make_epub_image_item("pic", "images/foo#bar.png", size=(6, 7)),
    )

    assert document.get_document_embedded_image(0).size == (6, 7)


def test_epub_document_rejects_protocol_relative_embedded_image(tmp_path):
    document = make_epub_document(
        tmp_path,
        '<html><body><h1>Intro</h1><p><img src="//cdn.example.com/pic.png" alt="Remote"></p></body></html>',
        make_epub_image_item("pic", "images/pic.png", size=(6, 7)),
    )

    with pytest.raises(DocumentIOError, match="Remote images"):
        document.get_document_embedded_image(0)


def test_epub_document_does_not_match_embedded_image_by_partial_suffix(tmp_path):
    document = make_epub_document(
        tmp_path,
        '<html><body><h1>Intro</h1><p><img src="cover.png" alt="Cover"></p></body></html>',
        make_epub_image_item("backcover", "chapters/backcover.png", size=(3, 4)),
        make_epub_image_item("cover", "chapters/cover.png", size=(6, 7)),
    )

    assert document.get_document_embedded_image(0).size == (6, 7)


def test_epub_document_does_not_choose_ambiguous_basename_fallback(tmp_path):
    document = make_epub_document(
        tmp_path,
        '<html><body><h1>Intro</h1><p><img src="pic.png" alt="Picture"></p></body></html>',
        make_epub_image_item("pic1", "images/pic.png", size=(3, 4)),
        make_epub_image_item("pic2", "figures/pic.png", size=(6, 7)),
    )

    with pytest.raises(DocumentIOError):
        document.get_document_embedded_image(0)


def test_epub_document_does_not_choose_unique_basename_fallback(tmp_path):
    document = make_epub_document(
        tmp_path,
        '<html><body><h1>Intro</h1><p><img src="../missing/pic.png" alt="Picture"></p></body></html>',
        make_epub_image_item("pic", "images/pic.png", size=(6, 7)),
    )

    with pytest.raises(DocumentIOError):
        document.get_document_embedded_image(0)


def test_epub_document_wraps_undecodable_embedded_image(tmp_path):
    document = make_epub_document(
        tmp_path,
        '<html><body><h1>Intro</h1><p><img src="../images/bad.svg" alt="Bad"></p></body></html>',
        make_epub_image_item(
            "bad",
            "images/bad.svg",
            media_type="image/svg+xml",
            content=b"<svg></svg>",
        ),
    )

    with pytest.raises(DocumentIOError):
        document.get_document_embedded_image(0)


def test_html_content_hash_uses_embedded_image_bytes(tmp_path):
    def make_document(directory, image_src, image_bytes=None, filename=None):
        directory.mkdir()
        if image_bytes is not None:
            (directory / (filename or image_src)).write_bytes(image_bytes)
        html_path = directory / "book.html"
        html_path.write_text(
            f"""
            <html>
                <head><title>Book</title></head>
                <body><p>alpha <img src="{image_src}" alt="Picture"> omega</p></body>
            </html>
            """,
            encoding="utf-8",
        )
        document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
        document.read()
        return document

    red_image = make_png_bytes(color=(255, 0, 0))
    blue_image = make_png_bytes(color=(0, 0, 255))
    first = make_document(tmp_path / "first", "pic.png", red_image)
    same_image_different_name = make_document(
        tmp_path / "same", "renamed.png", red_image
    )
    different_image = make_document(tmp_path / "different", "pic.png", blue_image)
    inline_image_src = "data:image/png;base64," + base64.b64encode(red_image).decode("ascii")
    inline_image = make_document(
        tmp_path / "inline",
        inline_image_src,
        None,
        filename="inline.png",
    )

    try:
        assert first.get_content_hash() == same_image_different_name.get_content_hash()
        assert first.get_content_hash() == inline_image.get_content_hash()
        assert first.get_content_hash() != different_image.get_content_hash()
    finally:
        first.close()
        same_image_different_name.close()
        different_image.close()
        inline_image.close()


def test_html_content_hash_resolves_remote_base_href_for_relative_images(tmp_path):
    def make_document(directory, base_href):
        directory.mkdir()
        html_path = directory / "book.html"
        html_path.write_text(
            f"""
            <html>
                <head><title>Book</title><base href="{base_href}"></head>
                <body><p>alpha <img src="pic.png" alt="Picture"> omega</p></body>
            </html>
            """,
            encoding="utf-8",
        )
        document = FileSystemHtmlDocument(DocumentUri.from_filename(html_path))
        document.read()
        return document

    first = make_document(tmp_path / "first", "https://cdn.example.com/one/")
    second = make_document(tmp_path / "second", "https://cdn.example.com/two/")

    try:
        assert first.get_content_hash() is not None
        assert second.get_content_hash() is not None
        assert first.get_content_hash() != second.get_content_hash()
    finally:
        first.close()
        second.close()


def test_odp_content_hash_uses_package_image_bytes(tmp_path):
    def make_document(filename, image_bytes):
        odp_path = tmp_path / filename
        with zipfile.ZipFile(odp_path, "w") as package:
            package.writestr("Pictures/pic.png", image_bytes)
        document = OdfPresentation(DocumentUri.from_filename(odp_path))
        document.parser = SimpleNamespace(title="Deck")
        document.slides = {
            "Slide": '<p>alpha <img src="Pictures/pic.png" alt="Picture"> omega</p>'
        }
        document.num_slides = 1
        document._is_read = True
        return document

    first = make_document("first.odp", make_png_bytes(color=(255, 0, 0)))
    second = make_document("second.odp", make_png_bytes(color=(0, 0, 255)))

    try:
        assert first.get_content_hash() != second.get_content_hash()
        image_info = first.get_page(0).get_embedded_image_info(0)
        image = first.get_page(0).get_embedded_image(0)
        assert image_info.src == "Pictures/pic.png"
        assert image.size == (3, 2)
    finally:
        first.close()
        second.close()


def test_epub_content_hash_uses_embedded_image_bytes(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    chapter_content = (
        '<html><body><h1>Intro</h1><p>alpha '
        '<img src="../images/pic.png" alt="Picture"> omega</p></body></html>'
    )
    first = make_epub_document(
        first_dir,
        chapter_content,
        make_epub_image_item(
            "pic",
            "images/pic.png",
            content=make_png_bytes(color=(255, 0, 0)),
        ),
    )
    second = make_epub_document(
        second_dir,
        chapter_content,
        make_epub_image_item(
            "pic",
            "images/pic.png",
            content=make_png_bytes(color=(0, 0, 255)),
        ),
    )

    try:
        assert first.get_content_hash() != second.get_content_hash()
    finally:
        first.close()
        second.close()


def test_image_io_serializes_rgba_as_jpeg():
    image = ImageIO.from_pil(Image.new("RGBA", (2, 2), (255, 0, 0, 128)))

    jpeg_bytes = image.as_bytes(format="JPEG")

    assert jpeg_bytes.startswith(b"\xff\xd8")


def test_image_io_preserves_palette_colors_for_byte_loaded_images():
    image = ImageIO.from_bytes(make_palette_png_bytes())

    assert image.mode == "RGB"
    assert [image.to_pil().getpixel((x, 0)) for x in range(2)] == [
        (255, 0, 0),
        (0, 255, 0),
    ]


@pytest.mark.parametrize(
    ("mode", "pixels", "expected_data", "expected_alpha"),
    (
        (
            "RGBA",
            [(255, 0, 0, 255), (0, 255, 0, 0)],
            bytes([255, 0, 0, 0, 255, 0]),
            bytes([255, 0]),
        ),
        (
            "LA",
            [(20, 255), (100, 0)],
            bytes([20, 20, 20, 100, 100, 100]),
            bytes([255, 0]),
        ),
    ),
)
def test_image_io_uses_wx_alpha_buffer_for_images_with_alpha(
    monkeypatch,
    mode,
    pixels,
    expected_data,
    expected_alpha,
):
    captured = {}

    class FakeWxImage:
        def ConvertToBitmap(self):
            return "bitmap"

    def fake_image_from_buffer(width, height, data, alpha=None):
        captured["width"] = width
        captured["height"] = height
        captured["data"] = bytes(data)
        captured["alpha"] = bytes(alpha) if alpha is not None else None
        return FakeWxImage()

    monkeypatch.setattr(
        "bookworm.image_io.wx.ImageFromBuffer",
        fake_image_from_buffer,
    )
    pil_image = Image.new(mode, (2, 1))
    pil_image.putdata(pixels)
    image = ImageIO.from_pil(pil_image)

    assert image.to_wx_bitmap() == "bitmap"
    assert captured == {
        "width": 2,
        "height": 1,
        "data": expected_data,
        "alpha": expected_alpha,
    }


def test_embedded_image_dialog_normalizes_save_format_suffix():
    output_path, image_format = EmbeddedImageDialog.get_save_target("cover.webp", 0)
    assert output_path.name == "cover.png"
    assert image_format == "PNG"

    output_path, image_format = EmbeddedImageDialog.get_save_target("cover.png", 1)
    assert output_path.name == "cover.jpg"
    assert image_format == "JPEG"


def test_embedded_image_dialog_confirms_normalized_target_overwrite(tmp_path):
    existing_target = tmp_path / "cover.png"
    existing_target.write_bytes(b"existing")
    selected_path = tmp_path / "cover.webp"

    output_path, image_format = EmbeddedImageDialog.get_save_target(selected_path, 0)

    assert output_path == existing_target
    assert image_format == "PNG"
    assert EmbeddedImageDialog.should_confirm_overwrite_after_suffix_normalization(
        selected_path,
        output_path,
    )
    assert not EmbeddedImageDialog.should_confirm_overwrite_after_suffix_normalization(
        existing_target,
        existing_target,
    )
    assert not EmbeddedImageDialog.should_confirm_overwrite_after_suffix_normalization(
        tmp_path / "new.webp",
        tmp_path / "new.png",
    )


def test_embedded_image_dialog_converts_cmyk_images_for_png_save():
    image = Image.new("CMYK", (2, 2))

    prepared_image = EmbeddedImageDialog.prepare_image_for_save(image, "PNG")
    png_bytes = BytesIO()
    prepared_image.save(png_bytes, format="PNG")

    assert prepared_image.mode == "RGB"
    assert png_bytes.getvalue().startswith(b"\x89PNG")


def test_structural_navigation_speech_does_not_repeat_generic_image_label():
    message, prefix = _get_structural_navigation_speech(
        "[Image]",
        "Image",
        SemanticElementType.FIGURE,
    )

    assert message == "Image"
    assert prefix == ""


def test_reader_ctrl_enter_opens_embedded_image(reader, view):
    document = SyntheticImageDocument(
        "[Cover]",
        {SemanticElementType.FIGURE: [(0, 7)]},
        image_infos=(ImageElementInfo(TextRange(0, 7), "cover.png", "Cover", "cover.png"),),
        images=(ImageIO.from_bytes(make_png_bytes(size=(8, 9))),),
    )
    document.read()
    reader.set_document(document)

    assert reader.handle_special_action_for_position(0) is True
    image, title, suggested_filename = view.image_dialog_args
    assert image.size == (8, 9)
    assert title == "Cover - Image View"
    assert suggested_filename == "cover.png"


def test_reader_ctrl_enter_activates_link_when_embedded_image_fails(reader, view):
    opened_urls = []
    invalid_actions = []
    view.go_to_webpage = opened_urls.append
    view.notify_invalid_action = lambda: invalid_actions.append(True)
    document = SyntheticImageDocument(
        "[Cover]",
        {
            SemanticElementType.FIGURE: [(0, 7)],
            SemanticElementType.LINK: [(0, 7)],
        },
        image_infos=(
            ImageElementInfo(
                TextRange(0, 7),
                "https://example.com/cover.png",
                "Cover",
                "cover.png",
            ),
        ),
        image_error=DocumentIOError("Remote images are not supported"),
        link_target=LinkTarget(url="https://example.com", is_external=True),
    )
    document.read()
    reader.set_document(document)

    assert reader.handle_special_action_for_position(0) is True
    assert opened_urls == ["https://example.com"]
    assert invalid_actions == []
    assert view.image_dialog_args is None


def test_reader_ctrl_enter_uses_document_order_after_backward_image_navigation(reader, view):
    document = SyntheticImageDocument(
        "[One]\n[Two]",
        {SemanticElementType.FIGURE: [(0, 5), (6, 11)]},
        image_infos=(
            ImageElementInfo(TextRange(0, 5), "One.png", "One", "One.png"),
            ImageElementInfo(TextRange(6, 11), "Two.png", "Two", "Two.png"),
        ),
        images=(
            ImageIO.from_bytes(make_png_bytes(size=(1, 1))),
            ImageIO.from_bytes(make_png_bytes(size=(2, 1))),
        ),
    )
    document.read()
    reader.set_document(document)

    reader.get_semantic_element(SemanticElementType.FIGURE, forward=False, anchor=20)
    assert reader.handle_special_action_for_position(6) is True
    image, title, suggested_filename = view.image_dialog_args
    assert image.size == (2, 1)
    assert title == "Two - Image View"
    assert suggested_filename == "Two.png"
