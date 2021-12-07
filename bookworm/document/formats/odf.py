# coding: utf-8

from __future__ import annotations
import sys
from functools import lru_cache
from odf import opendocument

# Hack to fix some pyinstaller issues
sys.modules["opendocument"] = opendocument


from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from lxml.html import fromstring as ParseHtml, tostring as SerializeHtml
from bs4 import BeautifulSoup
from odf.odf2xhtml import ODF2XHTML
from bookworm import typehints as t
from bookworm.paths import home_data_path
from bookworm.concurrency import process_worker
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
from bookworm.utils import generate_file_md5, escape_html, NEWLINE
from bookworm.document.uri import DocumentUri
from bookworm.logger import logger
from .. import (
    BaseDocument,
    BasePage,
    DummyDocument,
    BookMetadata,
    Section,
    Pager,
    DocumentCapability as DC,
    TreeStackBuilder,
    ChangeDocument,
    DocumentCapability as DC,
    DocumentError,
    DocumentEncryptedError,
)


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
                f"<title>{escape_html(self.title)}<title>",
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
            reason="Docx converted to html",
        )


class OdpSlide(BasePage):
    """Represents a slide in an open document presentation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        html_string = self.section.data["html_content"]
        (
            self.text,
            self.semantic_elements,
            self.style_info,
        ) = self.extract_info_and_structure(html_string)

    def extract_info_and_structure(self, html_string):
        parsed = StructuredHtmlParser.from_string(html_string)
        return parsed.get_text(), parsed.semantic_elements, parsed.styled_elements

    def get_text(self):
        return self.text

    def get_style_info(self) -> dict:
        return self.style_info

    def get_semantic_structure(self) -> dict:
        return self.semantic_elements


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
        for (idx, (slide_title, slide_html)) in enumerate(self.slides.items()):
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
            retval[slide_title] = BeautifulSoup(
                SerializeHtml(fieldset), "lxml"
            ).decode_contents()
        return retval
