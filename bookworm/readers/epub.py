from contextlib import suppress
import ebooklib
from ebooklib import epub
from ebooklib.utils import parse_html_string
from markupsafe import Markup
from ..logger import logger
from .base import BaseEBookReader, Book, TOCItem


log = logger.getChild(__name__)
log = logger.getChild(__name__)


class EPUBReader(BaseEBookReader):

    format = "epub"
    name = "Electronic Publications"
    extensions = ("*.epub",)

    def read(self):
        self.ebook = epub.read_epub(self.ebook_path)

    def get_content(self, item):
        content = self.ebook.get_item_with_href(item.data["obj"].href)
        if content is None:
            return item.title
        body_content = content.get_content()
        return parse_html_string(body_content).text_content().strip()

    @property
    def toc_tree(self):
        return self._get_toc_tree(self.ebook.toc)

    def _get_toc_tree(self, toc_list):
        toc = []
        for item in toc_list:
            if isinstance(item, epub.Link):
                chapt = TOCItem(title=item.title, data={"obj": item})
                toc.append(chapt)
            elif type(item) is tuple:
                # We've got a section
                sect = TOCItem(title=item[0].title, data={"obj": item[0]})
                children = self._get_toc_tree(toc_list=item[1])
                sect.children.extend(children)
                toc.append(sect)
            else:
                raise ValueError(f"Unknown TOC element {item}.")
        return toc

    @property
    def metadata(self):
        info = dict(
            title=self.ebook.title,
            author=self.ebook.get_metadata("DC", "creator")[0][0],
            publisher=self.ebook.get_metadata("DC", "publisher")[0][0]
        )
        with suppress(IndexError):
            info["publication_year"] =self.ebook.get_metadata("DC", "date")[0][0]
        return Book(**info)
