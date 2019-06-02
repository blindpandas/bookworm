import os
import fitz
from ..logger import logger
from ..utils import cached_property
from .base import (
    Pager,
    PaginatedBaseDocument,
    PaginatedTOCItem,
    BookMetadata,
    PaginationError
)


log = logger.getChild(__name__)


class FitzDocument(PaginatedBaseDocument):

    format = "pdf"
    name = "Portable Document Format"
    extensions = ("*.pdf",)

    def __getitem__(self, index):
        assert self._ebook is not None, "The book has not been loaded yet, use `read` to load it."
        if index not in self:
            raise PaginationError(f"Page {index} is out of range.")
        return self._ebook[index]

    def __len__(self):
        assert self._ebook is not None, "The book has not been loaded yet, use `read` to load it."
        return self._ebook.pageCount

    def read(self):
        self._ebook = fitz.open(self.ebook_path)

    def close(self):
        self._ebook.close()
        super().close()

    def _text_from_page(self, page):
        bloks = page.getTextBlocks()
        text = [blk[4].replace("\n", " ") for blk in bloks]
        return "\r\n".join(text)

    def get_content(self, item):
        content = "\r\n\f\r\n".join(self._text_from_page(self[p]) for p in item.pager)
        return content

    def get_page_content(self, page_number):
        return self._text_from_page(self[page_number])

    @cached_property
    def toc_tree(self):
        toc_info = self._ebook.getToC()
        max_page = len(self) - 1
        root_item = PaginatedTOCItem(
            title=self.metadata.title,
            pager=Pager(first=0, last=len(self))
        )
        toc = [root_item]
        for (index, (level, title, start_page, *extra)) in enumerate(toc_info):
            try:
                curr_index = index
                next_item = toc_info[curr_index + 1]
                while next_item[0] != level:
                    curr_index += 1
                    next_item = toc_info[curr_index]
            except IndexError:
                next_item = None
            last_page = max_page if next_item is None else (next_item[2] - 2)
            pgn = Pager(first=start_page - 1, last=last_page)
            chapt = PaginatedTOCItem(title=title, pager=pgn)
            if level  == 1:
                toc.append(chapt)
                continue
            parent_lvl  = level - 1
            parent =toc[-1]
            while True:
                if parent_lvl > 1:
                    parent = parent.children[-1]
                    parent_lvl -= 1
                    continue
                parent.children.append(chapt)
                break
        return toc

    @cached_property
    def metadata(self):
        meta = self._ebook.metadata
        to_str = lambda value: value or ""
        return BookMetadata(
            title=meta["title"] or os.path.split(self._ebook_path)[-1][:-4],
            author=to_str(meta["author"]),
            publication_year=to_str(meta["creationDate"])
        )


class FitzEPUBDocument(FitzDocument):

    format = "epub"
    name = "Electronic Publications"
    extensions = ("*.epub",)

