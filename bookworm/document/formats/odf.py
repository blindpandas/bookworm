
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import PurePosixPath
from urllib import parse as urllib_parse
from zipfile import BadZipFile, ZipFile

from odf import opendocument

# Hack to fix some pyinstaller issues
sys.modules["opendocument"] = opendocument


from dataclasses import dataclass
from functools import cached_property

from bs4 import BeautifulSoup
from lxml.html import fromstring as ParseHtml
from lxml.html import tostring as SerializeHtml
from odf.odf2xhtml import ODF2XHTML

from bookworm import typehints as t
from bookworm.image_io import ImageIO
from bookworm.document.uri import DocumentUri
from bookworm.logger import logger
from bookworm.paths import home_data_path
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
from bookworm.utils import NEWLINE, escape_html, generate_file_md5

from .. import (
    BaseDocument,
    BasePage,
    BookMetadata,
    ChangeDocument,
    DocumentIOError,
    DummyDocument,
    Pager,
    Section,
    TreeStackBuilder,
)
from .. import DocumentCapability as DC

log = logger.getChild(__name__)


@dataclass
class OdfParser:
    """Parses ODF documents and converts them to HTML."""

    odf_filename: t.PathLike

    def __post_init__(self):
        self.title = self.odf_filename.stem.strip()

    def get_converted_filename(self):
        storage_area = home_data_path("odf_as_html")
        storage_area.mkdir(parents=True, exist_ok=True)
        target_file = storage_area / f"{generate_file_md5(self.odf_filename)}.html"
        if not target_file.exists():
            target_file.write_text(self.as_html, encoding="utf-8")
        return target_file

    @cached_property
    def as_html(self):
        with open(self.odf_filename, "rb") as odf:
            converter = ODF2XHTML(generate_css=False, embedable=True)
            converter.set_embedable()
            converter.load(odf)
            return self.make_proper_html(converter.xhtml())

    def make_proper_html(self, html_string):
        html_body = SerializeHtml(ParseHtml(html_string).body, encoding="unicode")
        return NEWLINE.join(
            [
                "<!doctype html>",
                "<html><head>",
                '<meta charset="utf-8" />',
                f"<title>{escape_html(self.title)}</title>",
                "</head>",
                html_body,
                "</html>",
            ]
        )


class OdfTextDocument(DummyDocument):
    format = "odt"
    # Translators: the name of a document file format
    name = _("Open Document Text")
    extensions = ("*.odt",)
    capabilities = DC.ASYNC_READ

    def read(self):
        odf_file_path = self.get_file_system_path()
        parser = OdfParser(odf_file_path)
        converted_file = parser.get_converted_filename()
        raise ChangeDocument(
            old_uri=self.uri,
            new_uri=DocumentUri.from_filename(converted_file),
            reason="ODF converted to html",
        )


class OdpSlide(BasePage):
    """Represents a slide in an open document presentation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        html_string = self.section.data["html_content"]
        self.html_string = html_string
        (
            self.structure,
            self.text,
            self.storage_text,
            self.semantic_elements,
            self.style_info,
            self.text_position_map,
        ) = self.extract_info_and_structure(html_string)

    def extract_info_and_structure(self, html_string):
        parsed = StructuredHtmlParser.from_string(html_string)
        return (
            parsed,
            parsed.get_text(),
            parsed.get_storage_text(),
            parsed.semantic_elements,
            parsed.styled_elements,
            parsed.text_position_map,
        )

    def get_text(self):
        return self.text

    def get_storage_text(self):
        return self.storage_text

    def get_legacy_text(self):
        if hasattr(self, "_legacy_text"):
            return self._legacy_text
        self._legacy_text = StructuredHtmlParser.from_string(
            self.html_string,
            include_images=False,
        ).get_text()
        return self._legacy_text

    def get_text_position_map(self):
        return self.text_position_map

    def iter_content_hash_images(self):
        return tuple(
            (
                storage_range,
                self._get_embedded_image_content_hash_identity(image_info),
            )
            for image_info, storage_range in self.structure.iter_image_storage_ranges()
        )

    def _get_embedded_image_content_hash_identity(self, image_info):
        src = image_info.src
        if src.lower().startswith("data:image/"):
            try:
                return ("bytes", ImageIO.data_uri_to_bytes(src))
            except Exception:
                log.warning("Failed to hash embedded data URI image.", exc_info=True)
                return None
        parsed_src = urllib_parse.urlsplit(src)
        if parsed_src.scheme or parsed_src.netloc:
            return ("src", src.strip().encode())
        return self.document.get_package_image_content_hash_identity(src)

    def get_style_info(self) -> dict:
        return self.style_info

    def get_semantic_structure(self) -> dict:
        return self.semantic_elements

    def get_embedded_image_info(self, image_index: int):
        return self.structure.get_image_info(image_index)

    def get_embedded_image(self, image_index: int) -> ImageIO:
        image_info = self.get_embedded_image_info(image_index)
        if image_info.src.lower().startswith("data:image/"):
            try:
                return ImageIO.from_data_uri(image_info.src)
            except Exception as e:
                raise DocumentIOError("Failed to decode embedded image") from e
        image_bytes = self.document.get_package_image_bytes(image_info.src)
        try:
            return ImageIO.from_bytes(image_bytes)
        except Exception as e:
            raise DocumentIOError("Failed to decode embedded image") from e


class OdfPresentation(BaseDocument):
    """An open document presentation."""

    format = "odp"
    # Translators: the name of a document file format
    name = _("Open Document Presentation")
    extensions = ("*.odp",)
    capabilities = (
        DC.ASYNC_READ
        | DC.TOC_TREE
        | DC.METADATA
        | DC.STRUCTURED_NAVIGATION
        | DC.LINKS
        | DC.TEXT_STYLE
    )

    def __len__(self):
        return self.num_slides

    @lru_cache(maxsize=1000)
    def get_page(self, index):
        return OdpSlide(self, index)

    @cached_property
    def language(self):
        return self.get_language(self.html_string, is_html=True)

    def read(self):
        super().read()
        odf_file_path = self.get_file_system_path()
        self.parser = OdfParser(odf_file_path)
        self.html_string = self.parser.as_html
        self.slides = self._generate_slides_from_html(self.html_string)
        self.num_slides = len(self.slides)

    @cached_property
    def toc_tree(self):
        root = Section(
            title=self.metadata.title,
            pager=Pager(first=0, last=self.num_slides - 1),
            level=1,
        )
        stack = TreeStackBuilder(root)
        for idx, (slide_title, slide_html) in enumerate(self.slides.items()):
            stack.push(
                Section(
                    title=slide_title,
                    pager=Pager(first=idx, last=idx),
                    level=2,
                    data={"html_content": slide_html},
                )
            )
        return root

    @cached_property
    def metadata(self):
        return BookMetadata(
            title=self.parser.title,
            author="",
        )

    def get_package_image_bytes(self, src: str) -> bytes:
        parsed_src = urllib_parse.urlsplit(src)
        if parsed_src.scheme or parsed_src.netloc:
            raise DocumentIOError("Remote images are not supported")
        image_path = PurePosixPath(urllib_parse.unquote(parsed_src.path))
        if image_path.is_absolute() or ".." in image_path.parts or not image_path.parts:
            raise DocumentIOError("Invalid ODF package image path")
        try:
            with ZipFile(self.get_file_system_path()) as package:
                return package.read(image_path.as_posix())
        except (BadZipFile, KeyError, OSError) as e:
            raise DocumentIOError(f"Could not resolve embedded image: {src}") from e

    def get_package_image_content_hash_identity(self, src: str):
        try:
            return ("bytes", self.get_package_image_bytes(src))
        except DocumentIOError:
            log.warning(f"Failed to hash ODF package image '{src}'.", exc_info=True)
            return None

    def _generate_slides_from_html(self, html_string):
        retval = {}
        html_body = ParseHtml(html_string).body
        for idx, fieldset in enumerate(html_body.findall("fieldset")):
            if (legend := fieldset[0]).tag == "legend":
                legend.tag = "h1"
                slide_title = legend.text
                if slide_title.startswith("page"):
                    slide_title = _("Slide {number}").format(number=idx + 1)
                    legend.text = slide_title
            retval[slide_title] = BeautifulSoup(SerializeHtml(fieldset), "lxml").decode_contents()
        return retval
