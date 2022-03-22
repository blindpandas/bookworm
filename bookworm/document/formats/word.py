# coding: utf-8

from __future__ import annotations
import os
import subprocess
import mammoth
from docx import Document as DocxDocumentReader
from pathlib import Path
from selectolax.parser import HTMLParser
from bookworm import app
from bookworm.paths import home_data_path, app_path
from bookworm.concurrency import threaded_worker, process_worker
from bookworm.utils import generate_file_md5, escape_html, NEWLINE
from bookworm.document.uri import DocumentUri
from bookworm.logger import logger
from .. import (
    DummyDocument,
    ChangeDocument,
    DocumentCapability as DC,
    DocumentError,
    DocumentEncryptedError,
)


log = logger.getChild(__name__)
TAGS_TO_UNWRAP = []
TAGS_TO_REMOVE = [
    "img",
    "style",
]


class WordDocument(DummyDocument):

    format = "docx"
    # Translators: the name of a document file format
    name = _("Word Document")
    extensions = ("*.docx",)
    capabilities = DC.ASYNC_READ

    def read(self):
        docx_file_path = self.get_file_system_path()
        converted_file = process_worker.submit(
            self.get_converted_filename, docx_file_path
        ).result()
        raise ChangeDocument(
            old_uri=self.uri,
            new_uri=DocumentUri.from_filename(converted_file),
            reason="Docx converted to html",
        )

    @classmethod
    def get_converted_filename(cls, filename):
        storage_area = home_data_path("docx_as_html")
        storage_area.mkdir(parents=True, exist_ok=True)
        target_file = storage_area / f"{generate_file_md5(filename)}.html"
        if not target_file.exists():
            with open(filename, "rb") as docx:
                result = mammoth.convert_to_html(docx, include_embedded_style_map=False)
                html_string = cls.make_proper_html(result.value, filename)
                target_file.write_text(html_string, encoding="utf-8")
        return target_file

    @classmethod
    def make_proper_html(cls, html_string, docx_file_path):
        parsed = HTMLParser(html_string)
        parsed.body.unwrap_tags(TAGS_TO_UNWRAP)
        parsed.strip_tags(TAGS_TO_REMOVE)
        html_string = parsed.body.html
        docx = DocxDocumentReader(docx_file_path)
        props = docx.core_properties
        doc_title = props.title.strip()
        if not doc_title or doc_title.lower() == "word document":
            doc_title = docx_file_path.stem.strip()
        doc_author = escape_html(props.author or "")
        return NEWLINE.join(
            [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                '<meta charset="utf-8"/>',
                f'<meta name="author" content="{doc_author}"/>',
                f"<title>{escape_html(doc_title)}</title>",
                "</head>",
                html_string,
                "</html>",
            ]
        )


class Word97Document(DummyDocument):

    format = "doc"
    # Translators: the name of a document file format
    name = _("Word 97 - 2003 Document")
    extensions = ("*.doc",)
    capabilities = DC.ASYNC_READ

    def read(self):
        converted_file = threaded_worker.submit(
            self.get_converted_filename, self.get_file_system_path()
        ).result()
        raise ChangeDocument(
            old_uri=self.uri,
            new_uri=DocumentUri.from_filename(converted_file),
            reason="Doc converted to docbook",
        )

    @classmethod
    def get_converted_filename(cls, filename):
        storage_area = cls.get_storage_area()
        target_file = storage_area / f"{generate_file_md5(filename)}.docbook"
        if not target_file.exists():
            docbook_content = cls.convert_to_docbook(filename)
            target_file.write_bytes(docbook_content)
        return target_file

    @classmethod
    def convert_to_docbook(cls, filename):
        args = [cls.get_antiword_executable_path(), "-x", "db", filename]
        creationflags = subprocess.CREATE_NO_WINDOW
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        ret = subprocess.run(
            args,
            capture_output=True,
            creationflags=creationflags,
            startupinfo=startupinfo,
        )
        return ret.stdout

    @staticmethod
    def get_storage_area():
        storage_area = home_data_path(".doc_to_docbook")
        storage_area.mkdir(parents=True, exist_ok=True)
        return storage_area

    @staticmethod
    def get_antiword_executable_path():
        if app.is_frozen:
            return app_path("antiword", "bin", "antiword.exe")
        else:
            return (
                Path.cwd()
                / "scripts"
                / "executables"
                / "antiword"
                / "bin"
                / "antiword.exe"
            )
