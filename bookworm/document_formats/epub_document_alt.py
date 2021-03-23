# coding: utf-8

from functools import cached_property
from hashlib import md5
from tempfile import TemporaryDirectory
from pathlib import Path, PurePosixPath
from ebooklib.epub import read_epub
from inscriptis import get_text
from selectolax.parser import HTMLParser
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
from bookworm.logger import logger
from .epub_document import FitzEPUBDocument


log = logger.getChild(__name__)


class EpubPage(BasePage):

    def get_text(self):
        html = self._get_html_with_href(
            self.section.data['href'],
            self.document.epub
        )
        return self.normalize_text(get_text(html)).strip()

    def get_image(self, zoom_factor):
        raise NotImplementedError

    def _get_valid_href(self, href):
        href = PurePosixPath(href)
        parts = href.parts
        for i in range(len(parts)):
            yield str(PurePosixPath(*parts[i + 1:]))

    def _get_item_with_href(self, href, epub):
        html_item = epub.get_item_with_href(href)
        if html_item is None:            
            pfixes = self._get_valid_href(href)
            for pfix in pfixes:
                if (html_item := epub.get_item_with_href(pfix)):
                    return html_item
        return html_item

    def _get_html_with_href(self, href, epub):
        html_item = self._get_item_with_href(href, epub)
        if html_item is None:
            filename, html_id = href.split("#")
            item = self._get_item_with_href(filename, epub)
            parsed = HTMLParser(item.get_content().decode("utf8"))
            target = parsed.body.css_first(f"#{html_id}")
            if target:
                return target.html
            else:
                return href
        else:
            return html_item.get_body_content().decode("utf8")



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
        self.epub = read_epub(self.filename)
        super().read()

    def close(self):
        super().close()
        self.fitz_doc.close()

    @cached_property
    def language(self):
        return self.fitz_doc.language

    @cached_property
    def toc_tree(self):
        toc = self.fitz_doc._ebook.get_toc(simple=False)
        sect_count = len(toc)
        root = Section(
            document=self,
            title=self.metadata.title,
            pager=Pager(first=0, last=sect_count - 1),
            level=1,
        )
        stack = TreeStackBuilder(root)
        for (idx, (level, title, __, data)) in enumerate(toc):
            stack.push(Section(
                document=self,
                title=title,
                pager=Pager(first=idx, last=idx),
                level=level + 1,
                data=dict(href=data['name'])
            ))
        return root

    @cached_property
    def metadata(self):
        return self.fitz_doc.metadata
