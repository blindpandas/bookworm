# coding: utf-8

from __future__ import annotations
import zipfile
import fitz
import ftfy
from functools import cached_property, lru_cache
from hashlib import md5
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from pathlib import Path
from bookworm.paths import home_data_path
from bookworm.image_io import ImageIO
from bookworm.utils import recursively_iterdir
from bookworm.logger import logger
from .. import (
    BaseDocument,
    BasePage,
    Section,
    BookMetadata,
    Pager,
    DocumentCapability as DC,
    ChangeDocument,
    DocumentError,
    DocumentEncryptedError,
    DocumentRestrictedError,
)


log = logger.getChild(__name__)
fitz.Tools().mupdf_display_errors(False)


class FitzPage(BasePage):
    """Wrapps fitz.Page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fitz_page = self.document._ebook[self.index]

    def _text_from_page(self, page: fitz.Page) -> str:
        bloks = page.get_text_blocks()
        text = [blk[4].replace("\n", " ") for blk in bloks if blk[-1] == 0]
        text = "\r\n".join(text)
        return ftfy.fix_text(text, normalization="NFKC")

    def get_text(self):
        return self.normalize_text(self._text_from_page(self._fitz_page))

    def get_image(self, zoom_factor=1.0):
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        pix = self._fitz_page.get_pixmap(matrix=mat, alpha=False)
        return ImageIO(data=pix.samples, width=pix.width, height=pix.height)


class FitzDocument(BaseDocument):
    """The backend of this document type is Fitz (AKA MuPDF)."""

    format = None
    # Translators: the name of a document file format
    name = None
    extensions = ()
    capabilities = (
        DC.TOC_TREE
        | DC.METADATA
        | DC.GRAPHICAL_RENDERING
        | DC.IMAGE_EXTRACTION
        | DC.STRUCTURED_NAVIGATION
        | DC.LINKS
    )

    @lru_cache(maxsize=1000)
    def get_page(self, index: int) -> FitzPage:
        return FitzPage(self, index)

    def __len__(self) -> int:
        return self._ebook.pageCount

    def read(self, filetype=None):
        self.filename = self.get_file_system_path()
        try:
            self._ebook = fitz.open(self.filename, filetype=filetype)
            super().read()
        except RuntimeError as e:
            log.exception("Failed to open document", exc_info=True)
            if "drm" in e.args[0].lower():
                raise DocumentRestrictedError("Document is encrypted with DRM") from e
            raise DocumentError("Could not open document") from e
        if (
            self._ebook.isEncrypted
            and  (pwd := self.uri.view_args.get("decryption_key")) is not None
            and self._ebook.authenticate(pwd)
        ):
            return
        else:
            raise DocumentEncryptedError(self)

    def close(self):
        if self._ebook is None:
            return
        self._ebook.close()
        self._ebook = None
        super().close()

    @cached_property
    def toc_tree(self):
        toc_info = self._ebook.get_toc(simple=False)
        max_page = len(self) - 1
        root_item = Section(
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
        to_str = lambda value: "" if value is None else ftfy.fix_encoding(value).strip()
        return BookMetadata(
            title=to_str(meta["title"]) or Path(self.filename).stem,
            author=to_str(meta["author"]),
            publication_year=to_str(meta["creationDate"]),
        )

    def get_cover_image(self):
        return self.get_page_image(0)


class FitzFB2Document(FitzDocument):

    format = "fb2"
    # Translators: the name of a document file format
    name = _("Fiction Book (FB2)")
    extensions = ("*.fb2", "*.fb2.zip", "*.fbz")

    def read(self):
        self.filename = self.get_file_system_path()
        if not zipfile.is_zipfile(self.filename):
            return super().read()
        fb2_data = self.get_fb2_file_data()
        try:
            self._ebook = fitz.open(stream=fb2_data, filetype="fb2")
            BaseDocument.read(self)
        except Exception as e:
            raise DocumentError from e
        raise DocumentError("Invalid FB2 file")

    def get_fb2_file_data(self):
        with zipfile.ZipFile(self.filename, "r") as ziparchive:
            for fname in ziparchive.namelist():
                if fname.endswith("fb2"):
                    return ziparchive.read(fname)


class FitzXpsDocument(FitzDocument):

    format = "xps"
    # Translators: the name of a document file format
    name = _("XPS Document")
    extensions = ("*.xps", "*.oxps")


class FitzCBZDocument(FitzDocument):

    format = "cbz"
    # Translators: the name of a document file format
    name = _("Comic Book Archive")
    extensions = ("*.cbz",)
