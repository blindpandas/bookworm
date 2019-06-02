import os
from .logger import logger
from .document_formats import FitzDocument, FitzEPUBDocument, PaginationError


log = logger.getChild(__name__)


class EBookReader:

    # A list of document classes
    # Each class supports a different file format
    document_classes = (FitzEPUBDocument, FitzDocument)

    def __init__(self, view):
        self.supported_ebook_formats = {cls.format: cls for cls in self.document_classes}
        self.view = view
        self.document = None
        self.__state = {}

    def load(self, ebook_path):
        if self.document is not None:
            raise RuntimeError(f"Cannot open another book with this EBookReader.\r\n\
            A Book is already openned.\r\n\
            PleaseCreate a new instance.")
        ebook_format = os.path.splitext(ebook_path)[-1].lstrip(".")
        if ebook_format not in self.supported_ebook_formats:
            raise IOError(f"Unsupported ebook format {ebook_format}.")
        document_cls = self.supported_ebook_formats[ebook_format]
        self.document = document_cls(ebook_path=ebook_path)
        self.document.read()
        self.supports_pagination = self.document.supports_pagination
        view_title = self.current_book.title
        if self.current_book.author:
            view_title += f" — by {self.current_book.author}"
        self.view.SetTitle(view_title)
        self.view.addTocTree(self.document.toc_tree)
        self.active_item = self.document.toc_tree[0]

    def unload(self):
        self.document.close()

    @property
    def ready(self):
        return self.document is not None

    @property
    def active_item(self):
        return self.__state.get("active_item")

    @active_item.setter
    def active_item(self, value):
        if value is self.active_item:
            return
        if self.active_item is not None and self.supports_pagination:
            self.active_item.pager.reset()
        self.__state["active_item"] = value
        self.view.tocTreeSetSelection(value)

    @property
    def current_page(self):
        return self.__state.get("current_page", 1)

    @current_page.setter
    def current_page(self, value):
        if value == self.current_page:
            return
        if value not in self.active_item.pager:
            self.active_item = self.toc_tree[0]
        self.__state["current_page"] = value
        self.active_item.pager.set_current(value)

    def get_item_content(self, item):
        if self.supports_pagination:
            return self.get_page_content(page_number=item.pager.first)
        else:
            return self.document.get_content(item=item)

    def get_page_content(self, page_number):
        try:
            page = self.document.get_page_content(page_number)
            return f"<--- Page ({page_number + 1}) --->\r\n\r\n" + page
        except PaginationError:
            return

    def navigate(self, to):
        assert to in ("next", "prev"), "The `to` argument must be either `next` or `prev`."
        pgn = self.active_item.pager
        try:
            page_number = getattr(pgn, to)
        except PaginationError:
            return
        content = self.get_page_content(page_number=page_number)
        self.current_page = pgn.current
        return content

    @property
    def current_book(self):
        return self.document.metadata

