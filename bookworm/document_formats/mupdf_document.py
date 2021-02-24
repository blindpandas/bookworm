# coding: utf-8

import os
import zipfile
import fitz
import ftfy
from functools import cached_property
from hashlib import md5
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from pathlib import Path
from bookworm.paths import home_data_path
from bookworm.image_io import ImageIO
from bookworm.utils import recursively_iterdir
from bookworm.document_formats.base import (
    BaseDocument,
    BasePage,
    Section,
    BookMetadata,
    Pager,
    DocumentCapability as DC,
    DocumentError,
    TreeStackBuilder,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


class FitzPage(BasePage):
    """Wrapps fitz.Page."""

    def _text_from_page(self, page: fitz.Page) -> str:
        bloks = page.getTextBlocks()
        text = [blk[4].replace("\n", " ") for blk in bloks if blk[-1] == 0]
        text = "\r\n".join(text)
        return ftfy.fix_text(text, normalization="NFKC")

    def get_text(self):
        return self._text_from_page(self.document._ebook[self.index])

    def get_image(self, zoom_factor=1.0):
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        pix = self.document._ebook[self.index].getPixmap(matrix=mat, alpha=True)
        return ImageIO(data=pix.samples, width=pix.width, height=pix.height)


class FitzDocument(BaseDocument):
    """The backend of this document type is Fitz (AKA MuPDF)."""

    format = None
    # Translators: the name of a document file format
    name = None
    extensions = ()
    capabilities = (
        DC.TOC_TREE | DC.METADATA | DC.GRAPHICAL_RENDERING | DC.IMAGE_EXTRACTION
    )

    def get_page(self, index: int) -> FitzPage:
        return FitzPage(self, index)

    def __len__(self) -> int:
        return self._ebook.pageCount

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ebook: fitz.Document = None

    def read(self, filetype=None):
        try:
            self._ebook = fitz.open(self.filename, filetype=filetype)
            super().read()
        except RuntimeError as e:
            raise DocumentError(*e.args)

    def close(self):
        if self._ebook is None:
            return
        self._ebook.close()
        self._ebook = None
        super().close()

    def is_encrypted(self):
        return bool(self._ebook.isEncrypted)

    def decrypt(self, password):
        return bool(self._ebook.authenticate(password))

    @cached_property
    def toc_tree(self):
        toc_info = self._ebook.getToC(simple=False)
        max_page = len(self) - 1
        root_item = Section(
            document=self,
            title=self.metadata.title,
            pager=Pager(first=0, last=max_page),
            data={"html_file": None},
        )
        _last_entry = None
        for (index, (level, title, start_page, infodict)) in enumerate(toc_info):
            try:
                curr_index = index
                next_item = toc_info[curr_index + 1]
                while next_item[0] != level:
                    curr_index += 1
                    next_item = toc_info[curr_index]
            except IndexError:
                next_item = None
            first_page = start_page - 1
            last_page = max_page if next_item is None else next_item[2] - 2
            if first_page < 0:
                first_page = 0 if _last_entry is None else _last_entry.pager.last
            if last_page < first_page:
                last_page += 1
            if not all(p >= 0 for p in (first_page, last_page)):
                continue
            if first_page > last_page:
                continue
            pgn = Pager(first=first_page, last=last_page)
            sect = Section(
                document=self,
                title=title,
                pager=pgn,
                data={"html_file": infodict.get("name")},
            )
            if level == 1:
                root_item.append(sect)
                _last_entry = sect
                continue
            elif not root_item:
                continue
            parent = root_item.children[-1]
            parent_lvl = level - 1
            while True:
                if (parent_lvl > 1) and parent.children:
                    parent = parent.children[-1]
                    parent_lvl -= 1
                    continue
                parent.append(sect)
                _last_entry = sect
                break
        return root_item

    @cached_property
    def metadata(self):
        meta = self._ebook.metadata
        to_str = lambda value: value or ""
        return BookMetadata(
            title=meta["title"] or os.path.split(self.filename)[-1][:-4],
            author=to_str(meta["author"]),
            publication_year=to_str(meta["creationDate"]),
        )


class FitzEPUBDocument(FitzDocument):

    format = "epub"
    # Translators: the name of a document file format
    name = _("Electronic Publication (EPUB)")
    extensions = ("*.epub",)

    def read(self):
        try:
            super().read()
        except DocumentError as e:
            if "drm" in e.args[0].lower():
                log.debug("Got an encrypted file, will try to decrypt it...")
                self._original_file_name = self.filename
                self.filename = self.make_unrestricted_file(self.filename)
                return super().read(filetype="epub")
            raise e
        self._book_package = zipfile.ZipFile(self.filename)

    def close(self):
        self._book_package.close()
        super().close()

    def _get_section_text(self, section):
        html_file = section.data["html_file"]
        if html_file is None:
            return ""
        html_file, content_id = html_file.split("#")
        parents = PosixPath(html_file).parts[:-1]
        html_doc = html.document_fromstring(self._book_zip.read(html_file))
        if content_id is not None:
            html_doc = html_doc.get_element_by_id(content_id)

    @staticmethod
    def make_unrestricted_file(filename):
        """Try to remove digital restrictions from the EPUB document."""
        hashed_filename = md5(filename.lower().encode("utf8")).hexdigest()
        processed_book = home_data_path(hashed_filename)
        if processed_book.exists():
            return str(processed_book)
        _temp = TemporaryDirectory()
        temp_path = Path(_temp.name)
        ZipFile(filename).extractall(temp_path)
        (temp_path / "META-INF\\encryption.xml").unlink()
        with ZipFile(processed_book, "w") as book:
            for file in recursively_iterdir(temp_path):
                book.write(file, file.relative_to(temp_path))
        _temp.cleanup()
        return str(processed_book)


class FitzFB2Document(FitzDocument):

    format = "fb2"
    # Translators: the name of a document file format
    name = _("Fiction Book (FB2)")
    extensions = ("*.fb2",)
