# coding: utf-8

import os
import regex
from functools import cached_property
from io import StringIO
from bookworm.document_formats.base import (
    FluidDocument,
    Section,
    Pager,
    BookMetadata,
    DocumentCapability as DC,
    DocumentError,
)
from bookworm.logger import logger


log = logger.getChild(__name__)
MORE_THAN_ONE_LINE = regex.compile(r"[\n]{2,}")


class PlainTextDocument(FluidDocument):
    """For plain text files"""

    format = "txt"
    # Translators: the name of a document file format
    name = _("Plain Text File")
    extensions = ("*.txt",)
    capabilities = DC.FLUID_PAGINATION

    def read(self):
        self.text_buffer = StringIO()
        with open(self.filename, "r", encoding="utf8") as file:
            self.text_buffer.write(file.read())
        super().read()

    def get_content(self):
        return MORE_THAN_ONE_LINE.sub("\n", self.text_buffer.getvalue())

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
