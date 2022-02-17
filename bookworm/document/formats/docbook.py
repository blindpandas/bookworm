# coding: utf-8

from __future__ import annotations
import os
import contextlib
import subprocess
import dateparser
import lxml
from functools import cached_property
from pathlib import Path
from diskcache import Cache
from more_itertools import flatten, first as get_first_element
from bookworm import app
from bookworm.paths import home_data_path
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
            self.xml_tree = lxml.etree.fromstring(file.read())
        super().read()

    @cached_property
    def language(self):
        if (lang_tag := self.xml_tree.attrib.get("lang")):
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
        title = get_first_element(
            title,
            Path(self.get_file_system_path()).stem
        )
        author_firstname = get_first_element(
            xml_tree.xpath("/book/bookinfo/author/firstname//text()"),
            ""
        )
        author_surname = get_first_element(
            xml_tree.xpath("/book/bookinfo/author/surname//text()"),
            ""
        )
        author = " ".join([author_firstname, author_surname,])
        publisher = get_first_element(
            xml_tree.xpath("/book/bookinfo/corpname//text()"),
            ""
        )
        creation_date = xml_tree.xpath("/book/bookinfo/date//text()")
        if creation_date:
            parsed_date = dateparser.parse(
                creation_date[0],
                languages=[
                    self.language.two_letter_language_code,
                ]
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

    def _get_cache_directory(self):
        return str(home_data_path(".docbook_html_cache"))

    def get_html(self):
        if (html_string := getattr(self, "html_string", None)) is not None:
            return html_string
        cache_key = self.uri.to_uri_string()
        _cache = Cache(
            self._get_cache_directory(), eviction_policy="least-frequently-used"
        )
        if not (html_content := _cache.get(cache_key)):
            html_content = self._get_html_from_docbook()
            _cache.set(cache_key, html_content, expire=EXPIRE_TIMEOUT)
        return html_content

    def parse_html(self):
        return self.parse_to_full_text()

    def _get_html_from_docbook(self):
        xsltproc_path = self._get_xsltproc_path()
        xsltproc_executable = xsltproc_path / "xsltproc.exe"
        xsltproc_xhtml_xsl = xsltproc_path / "docbook-xsl-nons-1.79.2" / "xhtml" / "docbook.xsl"
        args = [
            xsltproc_executable,
            os.fspath(xsltproc_xhtml_xsl),
            os.fspath(self.filename),
            "--novalid",
            "--nonet",
            "--nowrite",
            "--encoding",
            "UTF8",
        ]
        creationflags = subprocess.CREATE_NO_WINDOW
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        ret = subprocess.run(
            args,
            capture_output=True,
            creationflags=creationflags,
            startupinfo=startupinfo,
        )
        html_bytes = ret.stdout
        html_bytes.replace(b"</p><p>", b"<br />")
        content_tree = lxml.etree.fromstring(html_bytes)
        block_classes = [
            "chapter",
            *[f"sect{i}" for i in range(1, 7)]
        ]
        span_block_elements = flatten(
            content_tree.xpath(f"//*[@class='{blk_cls}']")
            for blk_cls in block_classes
        )
        for elem in span_block_elements:
            elem.tag = "p"
        for el in content_tree.xpath('//ns:sup',namespaces={'ns':'http://www.w3.org/1999/xhtml'}):
            el.clear()
        return lxml.etree.tostring(content_tree, encoding="unicode")


    @staticmethod
    def _get_xsltproc_path():
        if app.is_frozen:
            return app_path("xsltproc")
        else:
            return Path.cwd() / "scripts" / "executables" / "xsltproc"
