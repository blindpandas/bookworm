# coding: utf-8

import mammoth
from docx import Document as DocxDocumentReader
from pathlib import Path
from bookworm.paths import home_data_path
from bookworm.concurrency import process_worker
from bookworm.utils import generate_file_md5, escape_html, NEWLINE
from bookworm.document_uri import DocumentUri
from bookworm.document_formats.base import (
    DummyDocument,
    ChangeDocument,
    DocumentCapability as DC,
    DocumentError,
    DocumentEncryptedError,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


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
        docx = DocxDocumentReader(docx_file_path)
        props = docx.core_properties
        doc_title = props.title.strip()
        if not doc_title or doc_title.lower() == "word document":
            doc_title = docx_file_path.stem.strip()
        doc_author = escape_html(props.author or "")
        return NEWLINE.join(
            [
                "<!doctype html>",
                "<html><head>",
                '<meta charset="utf-8" />',
                f'<meta name="author" content="{doc_author}">',
                f"<title>{escape_html(doc_title)}<title>",
                "</head><body>",
                html_string,
                "</body></html>",
            ]
        )
