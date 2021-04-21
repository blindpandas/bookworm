# coding: utf-8

import os
from functools import cached_property
from io import StringIO
from bookworm.document_formats.base import (
    SinglePageDocument,
    Section,
    Pager,
    BookMetadata,
    DocumentCapability as DC,
    DocumentError,
)
from bookworm.utils import normalize_line_breaks, remove_excess_blank_lines
from bookworm.logger import logger


log = logger.getChild(__name__)


class PlainTextDocument(SinglePageDocument):
    """For plain text files"""

    format = "txt"
    # Translators: the name of a document file format
    name = _("Plain Text File")
    extensions = ("*.txt",)
    capabilities = DC.SINGLE_PAGE

    def read(self):
        self.filename = self.get_file_system_path()
        self.text_buffer = StringIO()
        with open(self.filename, "r", encoding="utf8") as file:
            self.text_buffer.write(file.read())
        super().read()

    def get_content(self):
        text = remove_excess_blank_lines(self.text_buffer.getvalue())
        return normalize_line_breaks(text)

    def close(self):
        super().close()

    @cached_property
    def toc_tree(self):
        return Section(
            document=self,
            title="",
            pager=Pager(first=0, last=0),
        )

    @cached_property
    def metadata(self):
        return BookMetadata(
            title=os.path.split(self.filename)[-1][:-4],
            author="",
            publication_year="",
        )
