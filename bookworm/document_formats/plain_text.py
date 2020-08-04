# coding: utf-8

import io
from bookworm.utils import cached_property
from bookworm.document_formats.base import (
    BaseDocument,
    BasePage,
    Section,
    BookMetadata,
    DocumentCapability as DC,
    DocumentError,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


class PlainTextPage(BasePage):
    """Simulate a page for a plain text document."""

    def get_text(self):
        return ""

    def get_image(self, zoom_factor=1.0, enhance=False):
        raise NotImplementedError


class PlainTextDocument(BaseDocument):
    """For plain text files"""

    format = "txt"
    # Translators: the name of a document file format
    name = _("Plain Text File")
    extensions = ("*.txt",)
    capabilities = DC.FLUID_PAGINATION

    def get_page(self, index: int) -> PlainTextPage:
        return PlainTextPage

    def __len__(self) -> int:
        return self._ebook.pageCount

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_buffer: io.TextIOBase = None

    def read(self, filetype=None):
        super().read()

    def close(self):
        super().close()

    @cached_property
    def toc_tree(self):
        return Section(
            document=self,
            title=self.metadata.title,
            pager=Pager(first=0, last=max_page),
        )

    @cached_property
    def metadata(self):
        return BookMetadata(
            title=os.path.split(self.filename)[-1][:-4], author="", publication_year="",
        )
