from .logger import logger
from .readers import EPUBReader, FitzReader, PaginationError


log = logger.getChild(__name__)


class EBookController:

    # A list of reader classes
    # Each class supports a different file format
    reader_classes = (EPUBReader, FitzReader,)

    def __init__(self, view):
        self.supported_ebook_formats = {cls.format: cls for cls in self.reader_classes}
        self.view = view
        self.reader = None

    def open_ebook(self, ebook_path, format, **kwargs):
        if self.reader is not None:
            self.reader.close()
        if format not in self.supported_ebook_formats:
            raise IOError(f"Unsupported ebook format {format}.")
        reader_cls = self.supported_ebook_formats[format]
        self.reader = reader_cls(ebook_path=ebook_path)
        self.reader.read()
        self.active_item = None
        self.supports_pagination = self.reader.supports_pagination
        view_title = self.current_book.title
        if self.current_book.author:
            view_title += f" — by {self.current_book.author}"
        self.view.SetTitle(view_title)
        self.view.add_toc_tree(self.reader.toc_tree)

    @property
    def ready(self):
        return self.reader is not None

    def get_item_content(self, item):
        if self.supports_pagination:
            pgn = item.data["paginater"]
            return self.get_page_content(page_number=pgn.first)
        else:
            return self.reader.get_content(item=item)

    def get_page_content(self, page_number):
        try:
            page = self.reader.get_page_content(page_number)
            if page_number not in self.active_item.data["paginater"]:
                self.set_active_item(self.reader.toc_tree[0])
            self.active_item.data["paginater"].set_current(page_number)
            return f"<--- Page ({page_number + 1}) --->\r\n\r\n" + page
        except PaginationError:
            log.debug(f"Page out of range {page_number}.")

    def navigate(self, to):
        assert to in ("next", "prev"), "The `to` argument must be either `next` or `prev`."
        pgn = self.active_item.data["paginater"]
        try:
            page_number = getattr(pgn, to)
        except PaginationError:
            return
        return self.get_page_content(page_number=page_number)

    def set_active_item(self, to):
        if self.active_item is not None and self.supports_pagination:
            self.active_item.data["paginater"].reset()
        self.active_item = to

    @property
    def current_book(self):
        return self.reader.metadata

