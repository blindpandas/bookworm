# coding: utf-8

from __future__ import annotations
import os
import copy
import contextlib
import subprocess
import dateparser
import lxml
from functools import cached_property
from pathlib import Path
from more_itertools import flatten, first as get_first_element
from bookworm import app
from bookworm.paths import resources_path
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from .. import (
    BookMetadata,
    DocumentError,
    DocumentIOError,
)
from .html import BaseHtmlDocument


log = logger.getChild(__name__)
EXPIRE_TIMEOUT = 30 * 24 * 60 * 60


class DocbookDocument(BaseHtmlDocument):
    """Docbook is a format for writing technical documentation. It uses it's own markup."""

    format = "docbook"
    # Translators: the name of a document file format
    name = _("Docbook Document")
    extensions = ("*.docbook",)

    def read(self):
        self.filename = self.get_file_system_path()
        with open(self.filename, "rb") as file:
            content = file.read()
        try:
            self.xml_tree = lxml.etree.fromstring(content)
        except lxml.etree.XMLSyntaxError:
            xml_bytes = content.decode("utf-8", errors="replace").encode("utf-8")
            self.xml_tree = lxml.etree.fromstring(xml_bytes)
        super().read()

    @cached_property
    def language(self):
        if lang_tag := self.xml_tree.attrib.get("lang"):
            try:
                return LocaleInfo(lang_tag)
            except ValueError:
                pass
        plane_text = "\n".join(self.xml_tree.itertext(tag="para"))
        return self.get_language(plane_text, is_html=False)

    @cached_property
    def metadata(self):
        return self._get_book_metadata()

    def _get_book_metadata(self):
        xml_tree = self.xml_tree
        if not (title := xml_tree.xpath("/book/title//text()")):
            title = xml_tree.xpath("/book/bookinfo/title//text()")
        title = get_first_element(title, Path(self.get_file_system_path()).stem)
        author_firstname = get_first_element(
            xml_tree.xpath("/book/bookinfo/author/firstname//text()"), ""
        )
        author_surname = get_first_element(
            xml_tree.xpath("/book/bookinfo/author/surname//text()"), ""
        )
        author = " ".join(
            [
                author_firstname,
                author_surname,
            ]
        )
        publisher = get_first_element(
            xml_tree.xpath("/book/bookinfo/corpname//text()"), ""
        )
        creation_date = xml_tree.xpath("/book/bookinfo/date//text()")
        if creation_date:
            parsed_date = dateparser.parse(
                creation_date[0],
                languages=[
                    self.language.two_letter_language_code,
                ],
            )
            creation_date = self.language.format_datetime(
                parsed_date, date_only=True, format="long", localized=True
            )
        return BookMetadata(
            title=title,
            author=author,
            creation_date=creation_date,
            publisher=publisher,
        )

    def get_html(self):
        if (html_string := getattr(self, "html_string", None)) is not None:
            return html_string
        return self._get_html_from_docbook()

    def parse_html(self):
        return self.parse_to_full_text()

    def _get_html_from_docbook(self):
        xslt = lxml.etree.parse(os.fspath(self._get_xslt_resource_path()))
        transform = lxml.etree.XSLT(xslt)
        content_tree = transform(copy.copy(self.xml_tree))
        block_classes = ["chapter", *[f"sect{i}" for i in range(1, 7)]]
        span_block_elements = flatten(
            content_tree.xpath(f"//*[@class='{blk_cls}']") for blk_cls in block_classes
        )
        for elem in span_block_elements:
            elem.tag = "p"
        for el in content_tree.xpath(
            "//ns:sup", namespaces={"ns": "http://www.w3.org/1999/xhtml"}
        ):
            el.clear()
        return lxml.etree.tostring(content_tree, encoding="unicode")

    @staticmethod
    def _get_xslt_resource_path():
        return resources_path("xslt", "xhtml", "docbook.xsl")
