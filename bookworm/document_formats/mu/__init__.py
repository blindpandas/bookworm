# coding: utf-8

import os
import fitz
from bookworm.concurrency import QueueProcess
from bookworm.utils import cached_property
from bookworm.document_formats.base import (
    BaseDocument,
    Section,
    BookMetadata,
    Pager,
    DocumentError,
    PaginationError,
)
from bookworm.logger import logger
from . import _tools


log = logger.getChild(__name__)


class FitzDocument(BaseDocument):

    format = "pdf"
    # Translators: the name of a document file format
    name = _("Portable Document (PDF)")
    extensions = ("*.pdf",)
    supports_rendering = True

    def __getitem__(self, index):
        if index not in self:
            raise PaginationError(f"Page {index} is out of range.")
        return self._ebook[index]

    def __len__(self):
        return self._ebook.pageCount

    def read(self, filetype=None):
        try:
            self._ebook = fitz.open(self.filename, filetype=filetype)
        except RuntimeError as e:
            raise DocumentError(*e.args)
        super().read()

    def close(self):
        if self._ebook is None:
            return
        self._ebook.close()
        super().close()

    def is_encrypted(self):
        return bool(self._ebook.isEncrypted)

    def decrypt(self, password):
        return bool(self._ebook.authenticate(password))

    def _text_from_page(self, page):
        bloks = page.getTextBlocks(flags=fitz.TEXT_PRESERVE_WHITESPACE)
        text = [blk[4].replace("\n", " ") for blk in bloks]
        return "\r\n".join(text)

    def get_page_content(self, page_number):
        return self._text_from_page(self[page_number])

    @cached_property
    def toc_tree(self):
        toc_info = self._ebook.getToC()
        max_page = len(self) - 1
        root_item = Section(
            title=self.metadata.title, pager=Pager(first=0, last=max_page, current=0)
        )
        _last_entry = None
        for (index, (level, title, start_page)) in enumerate(toc_info):
            try:
                curr_index = index
                next_item = toc_info[curr_index + 1]
                while next_item[0] != level:
                    curr_index += 1
                    next_item = toc_info[curr_index]
            except IndexError:
                next_item = None
            first_page = start_page - 1
            last_page = max_page if next_item is None else next_item[-1] - 2
            if first_page < 0:
                first_page = 0 if _last_entry is None else _last_entry.pager.last
            if last_page < first_page:
                last_page += 1
            if not all(p >= 0 for p in (first_page, last_page)):
                continue
            if first_page > last_page:
                continue
            pgn = Pager(first=first_page, last=last_page, current=first_page)
            sect = Section(title=title, pager=pgn)
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

    @staticmethod
    def export_to_text(document_path, target_filename):
        args = (document_path, target_filename)
        process = QueueProcess(
            target=_tools.do_export_to_text, args=args, name="bookworm-exporter"
        )
        process.start()
        while True:
            value = process.queue.get()
            if value == -1:
                break
            yield value
        process.join()

    @staticmethod
    def search(document_path, request):
        args = (document_path, request)
        process = QueueProcess(
            target=_tools.do_search_book, args=args, name="bookworm-search"
        )
        process.start()
        while True:
            value = process.queue.get()
            if value == -1:
                break
            yield value
        process.join()


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
                log.debug("Got an encrypted file, attempting to decrypt it...")
                self._original_file_name = self.filename
                self.filename = _tools.make_unrestricted_file(self.filename)
                return super().read(filetype="epub")
            raise e
