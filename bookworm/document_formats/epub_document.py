# coding: utf-8

from functools import cached_property
from hashlib import md5
from zipfile import ZipFile
from tempfile import TemporaryDirectory
from pathlib import Path, PurePosixPath
from ebooklib.epub import read_epub
from inscriptis import get_text
from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser
from bookworm.paths import home_data_path
from bookworm.utils import recursively_iterdir
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
from .fitz_document import FitzPage, FitzDocument


log = logger.getChild(__name__)


class EpubPage(BasePage):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.epub = self.document.epub
        self.ziparchive = self.document.ziparchive

    def get_text(self):
        html = self._get_html_with_href(self.section.data['href'])
        return self.normalize_text(get_text(html)).strip()

    def get_image(self, zoom_factor):
        raise NotImplementedError

    def _get_item(self, href):
        if (html_element := self.epub.get_item_with_href(href)):
            return html_element
        href = PurePosixPath(href)
        parts = href.parts
        for i in range(len(parts)):
            possible_href = str(PurePosixPath(*parts[i - 1:]))
            if (html_item := self.epub.get_item_with_href(possible_href)):
                return html_item

    def parse_split_chapter(self, filename):
        split_anchors = self.document._split_section_anchor_ids[filename]
        self.document._split_section_content [filename] = {}
        chapter_content = self.ziparchive.read(filename).decode("utf-8")
        soup = BeautifulSoup(chapter_content, 'lxml')
        for this_anchor in reversed(split_anchors):
            this_tag = soup.find(
                attrs={"id":lambda x: x == this_anchor})
            markup_split = str(soup).split(str(this_tag))
            soup = BeautifulSoup(markup_split[0], 'lxml')
            # If the tag is None, it probably means the content is overlapping
            # Skipping the insert is the way forward
            if this_tag:
                this_markup = BeautifulSoup(
                    str(this_tag).strip() + markup_split[1], 'lxml')
                self.document._split_section_content[filename][this_anchor] = str(this_markup)
        # Remaining markup is assigned here
        self.document._split_section_content[filename][""] = str(soup)

    def _get_split_section_text(self, filename, html_id):
        if (anchor_info := self.document._split_section_content.get(filename, None)):
            return anchor_info[html_id]
        self.parse_split_chapter(filename)
        return self._get_split_section_text(filename, html_id)

    def _get_html_with_href(self, href):
        if (html_item := self._get_item(href)):
            if href not in self.document._split_section_anchor_ids:
                return html_item.get_content().decode("utf-8")
            else:
                return self._get_split_section_text(html_item.file_name, "")
        elif (html_item is None) and ("#" in href):
            file_part, fragment_part = href.split("#")
            if (html_element := self._get_item(file_part)):
                return self._get_split_section_text(html_element.file_name, fragment_part)
        raise RuntimeError(f"Could not extract text from section with href: {href} and filename: {filename}")



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
        self.ziparchive  = ZipFile(self.filename, "r")
        self._split_section_anchor_ids = {}
        self._split_section_content = {}
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
            href = data['name']
            stack.push(Section(
                document=self,
                title=title,
                pager=Pager(first=idx, last=idx),
                level=level + 1,
                data=dict(href=href)
            ))
            if "#" in href:
                filename, html_id = href.split("#")
                self._split_section_anchor_ids.setdefault(filename, []).append(html_id)
        return root

    @cached_property
    def metadata(self):
        return self.fitz_doc.metadata


class FitzEPUBDocument(FitzDocument):

    __internal__ = True

    def read(self, filetype=None):
        try:
            super().read(filetype)
        except DocumentEncryptedError:
            log.debug("Got an encrypted file, will try to decrypt it...")
            raise ChangeDocument(
                old_uri=self.uri,
                new_uri=self.uri.create_copy(format="drm_epub"),
                reason="Document is encrypted with DRM",
            )


class _DrmFitzEpubDocument(EpubDocument):
    """Fixes DRM encrypted epub documents."""

    __internal__ = True
    format = "drm_epub"

    def read(self):
        self._original_filename = self.get_file_system_path()
        try:
            self.filename = self.make_unrestricted_file(self._original_filename)
            self.uri = self.uri.create_copy(
                path=self.filename,
            )
            super().read()
        except Exception as e:
            raise DocumentError("Could not open DRM encrypted epub document") from e

    @staticmethod
    def make_unrestricted_file(filename):
        """
        Try to remove Digital Rights Management (DRM) type
        encryption from the EPUB document.
        
        Legal note:
        The removal of the encryption from the file does not involve any
        violation of any laws whatsoever, as long as the user has obtained
        the eBook using leditimate means, and the user intents to use the
        content in a manor that does not violate the law.
        """
        filepath = Path(filename)
        content_hash = md5()
        with open(filepath, 'rb') as ebook_file:
            for chunk in ebook_file:
                content_hash.update(chunk)
        identifier  = content_hash.hexdigest()
        processed_book = home_data_path(f"{identifier}.epub")
        if processed_book.exists():
            return str(processed_book)
        _temp = TemporaryDirectory()
        temp_path = Path(_temp.name)
        ZipFile(filename).extractall(temp_path)
        with ZipFile(processed_book, "w") as book:
            for file in recursively_iterdir(temp_path):
                if "encryption.xml" in file.name.lower():
                    continue
                book.write(file, file.relative_to(temp_path))
        _temp.cleanup()
        return str(processed_book)


