# coding: utf-8

import ftfy
from functools import cached_property
from hashlib import md5
from tempfile import TemporaryDirectory
from pathlib import Path
from inscriptis import get_text
from bookworm.image_io import ImageIO
from bookworm.document_formats.base import (
    BaseDocument,
    BasePage,
    Section,
    BookMetadata,
    Pager,
    DocumentCapability as DC,
    TreeStackBuilder,
    ChangeDocument,
    DocumentError,
    DocumentEncryptedError,
)
from bookworm.vendor.epub_parser import ParseEPUB
from bookworm.logger import logger
from .epub_document import FitzEPUBDocument


log = logger.getChild(__name__)


class EpubPage(BasePage):

    def get_text(self):
        html = self.document.content[self.index]
        return self.normalize_text(get_text(html)).strip()

    def get_image(self, zoom_factor):
        raise NotImplementedError



class EpubDocument(BaseDocument):

    format = "epub"
    # Translators: the name of a document file format
    name = _("Electronic Publication (EPUB)")
    extensions = ("*.epub",)
    capabilities = DC.TOC_TREE | DC.METADATA

    def __len__(self):
        return self.toc_tree.pager.last + 1

    def get_page(self, index):
        return EpubPage(self, index)

    def read(self):
        self.fitz_doc = FitzEPUBDocument(self.uri)
        self.fitz_doc.read()
        self.filename = self.get_file_system_path()
        self.tempdir = TemporaryDirectory()
        filemd5 = md5(self.filename.read_bytes()).hexdigest()
        self.epub = ParseEPUB(
            str(self.filename),
            self.tempdir.name,
            filemd5
        )
        self.epub.read_book()
        super().read()

    def close(self):
        super().close()
        self.tempdir.cleanup()

    @cached_property
    def language(self):
        return self.fitz_doc.language

    @property
    def content(self):
        return self._generated_content[1]

    @cached_property
    def _generated_content(self):
        toc, content, __ = self.epub.generate_content()
        return toc, content

    @cached_property
    def toc_tree(self):
        toc, content = self._generated_content
        sect_count = len(toc)
        root = Section(
            document=self,
            title=self.metadata.title,
            pager=Pager(first=0, last=sect_count - 1),
            level=1,
        )
        stack = TreeStackBuilder(root)
        for ((level, title, num), sect_content) in zip(toc, content):
            page_index = num - 1
            stack.push(Section(
                document=self,
                title=title,
                pager=Pager(page_index, last=page_index),
                level=level + 1,
            ))
        return root

    @cached_property
    def metadata(self):
        metadata = self.epub.generate_metadata() 
        return BookMetadata(
            title=metadata.title,
            author=metadata.author,
            publication_year=metadata.year,
            isbn=metadata.isbn
        )
