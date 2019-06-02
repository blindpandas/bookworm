import os
import fitz
from ..logger import logger
from .base import PaginatedBaseEBookReader, Book, TOCItem, Pagination, PaginationError


log = logger.getChild(__name__)


class FitzReader(PaginatedBaseEBookReader):

    format = "pdf"
    name = "Portable Document Format"
    extensions = ("*.pdf",)

    def __getitem__(self, index):
        assert self.ebook is not None, "The book has not been loaded yet, use `read` to load it."
        return self.ebook[index]

    def __len__(self):
        assert self.ebook is not None, "The book has not been loaded yet, use `read` to load it."
        return self.ebook.pageCount

    def read(self):
        self.ebook = fitz.open(self.ebook_path)

    def close(self):
        self.ebook.close()
        super().close()

    def _content_for_page(self, page):
        bloks = page.getTextBlocks()
        text = [blk[4].replace("\n", " ") for blk in bloks]
        return "\r\n".join(text)

    def get_content(self, item):
        pgn = item.data["paginater"]
        content = "\r\n\f\r\n".join(self._content_for_page(self[p]) for p in pgn)
        pgn.reset()
        return content

    def get_page_content(self, page_number):
        super().get_page_content(page_number)
        return self._content_for_page(self[page_number])

    @property
    def toc_tree(self):
        toc_info = self.ebook.getToC()
        max_page = len(self) - 1
        root_item = TOCItem(
            title=self.metadata.title,
            data={"paginater": Pagination(first=0, last=len(self))}
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
            pgn = Pagination(first=start_page - 1, last=last_page)
            chapt = TOCItem(title=title, data={"paginater": pgn})
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

    @property
    def metadata(self):
        meta = self.ebook.metadata 
        to_str = lambda value: value or ""
        return Book(
            title=meta["title"] or os.path.split(self.ebook_path)[-1][:-4],
            author=to_str(meta["author"]),
            publication_year=to_str(meta["creationDate"])
        )


class EPUBReader(FitzReader):

    format = "epub"
    name = "Electronic Publications"
    extensions = ("*.epub",)

