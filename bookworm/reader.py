# coding: utf-8

import os
from contextlib import suppress
from bookworm import typehints as t
from bookworm import app
from bookworm import config
from bookworm import database
from bookworm.i18n import is_rtl
from bookworm.document_formats import (
    FitzPdfDocument,
    FitzEPUBDocument,
    FitzFB2Document,
    PlainTextDocument,
    HtmlDocument,
    DocumentCapability,
    DocumentError,
    PaginationError,
)
from bookworm.document_formats.base import Section, BasePage
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    reader_section_changed,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


class ReaderError(Exception):
    """Base class for all reader exceptions."""


class ResourceDoesNotExist(ReaderError):
    """The file does not exist."""


class UnsupportedDocumentError(ReaderError):
    """File type/format is not supported."""


class EBookReader:
    """The controller that glues together the
    document model and the view model .
    """

    __slots__ = [
        "supported_ebook_formats",
        "document",
        "view",
        "__state",
        "current_book",
    ]

    # A list of document classes
    # Each class supports a different file format
    document_classes = (
        FitzPdfDocument,
        FitzEPUBDocument,
        FitzFB2Document,
        PlainTextDocument,
        HtmlDocument,
    )

    def __init__(self, view):
        self.supported_ebook_formats = {
            cls.format: cls for cls in self.document_classes
        }
        self.view = view
        self.reset()

    def reset(self):
        self.document = None
        self.__state = {}

    def load(self, ebook_path: t.PathLike) -> bool:
        ebook_format = self._detect_ebook_format(ebook_path)
        if ebook_format not in self.supported_ebook_formats:
            raise UnsupportedDocumentError(
                f"The file type {ebook_format} is not supported"
            )
        if not os.path.isfile(ebook_path):
            raise ResourceDoesNotExist(f"Could not open file: {ebook_path}")
        document_cls = self.supported_ebook_formats[ebook_format]
        try:
            self.document = document_cls(filename=ebook_path)
            self.document.read()
            result = self.view.try_decrypt_document(self.document)
            if not result:
                with suppress(Exception):
                    self.unload()
                return
        except DocumentError as e:
            self.reset()
            raise ReaderError("Failed to open document", e)
        self.current_book = self.document.metadata
        # Set the view parameters
        self.view.set_title(self.get_view_title(include_author=True))
        self.view.set_text_direction(is_rtl(self.document.language))
        self.view.add_toc_tree(self.document.toc_tree)
        self.__state.setdefault("current_page_index", -1)
        self.current_page = 0
        if config.conf["general"]["open_with_last_position"]:
            try:
                log.debug("Retreving last saved reading position from the database")
                pos_info = database.get_last_position(ebook_path.lower())
                if pos_info is not None:
                    page_number, pos = pos_info
                    log.debug("Navigating to the last saved position.")
                    self.go_to_page(page_number, pos)
            except:
                log.exception(
                    "Failed to restore last saved reading position", exc_info=True
                )
        reader_book_loaded.send(self)

    def unload(self):
        if self.ready:
            try:
                log.debug("Saving current position.")
                self.save_current_position()
                log.debug("Closing current document.")
                self.document.close()
            except:
                log.exception(
                    "An exception was raised while closing the ebook", exc_info=True
                )
                if app.debug:
                    raise
            finally:
                self.reset()
                reader_book_unloaded.send(self)

    def save_current_position(self):
        filename = self.document.filename
        # Some times we may need to shadow the original document with another
        #  one, for example when we decrypt it, or when we make it a11y friendly
        if getattr(self.document, "_original_file_name", None):
            filename = self.document._original_file_name
        database.save_last_position(
            filename.lower(),
            self.current_page,
            self.view.get_insertion_point(),
        )

    @property
    def ready(self) -> bool:
        return self.document is not None

    @property
    def active_section(self) -> Section:
        return self.__state.get("active_section")

    @active_section.setter
    def active_section(self, value: Section):
        if (self.active_section is not None) and (
            value.unique_identifier == self.active_section.unique_identifier
        ):
            return
        self.__state["active_section"] = value
        if self.document.has_toc_tree:
            self.view.set_state_on_section_change(value)
        reader_section_changed.send(self, active=value)

    @property
    def current_page(self) -> int:
        return self.__state["current_page_index"]

    @current_page.setter
    def current_page(self, value: int):
        if value == self.current_page:
            return
        if value not in self.document:
            raise PaginationError(
                f"Page {value} is out of range."
                f"Total number of pages in the document is: {len(self.document)}"
            )
        self.__state["current_page_index"] = value
        page = self.document[value]
        self.active_section = page.section
        self.view.set_state_on_page_change(page)
        reader_page_changed.send(self, current=page, prev=None)

    def get_current_page_object(self) -> BasePage:
        """Return the current page."""
        return self.document[self.current_page]

    def go_to_page(self, page_number: int, pos: int = 0) -> bool:
        self.current_page = page_number
        self.view.set_insertion_point(pos)

    def navigate(self, to: str, unit: str) -> bool:
        """
        Navigate to `to` by unit `unit`.
        Return `True` if navigation was successful, `False` otherwise.
        If unit is page and the target is in another section, this method
        returns False.
        """
        assert to in ("next", "prev"), f"Invalid value {to} for arg`to`."
        assert unit in ("page", "section"), f"Invalid value {unit} for arg`unit`."
        if unit == "page":
            step = 1 if to == "next" else -1
            next_move = self.current_page + step
            page = None if next_move not in self.document else self.document[next_move]
            if page is not None:
                if (to == "next" and not page.is_first_of_section) or (
                    to == "prev" and not page.is_last_of_section
                ):
                    self.current_page = next_move
                    return True
                else:
                    return False
        elif unit == "section":
            this_section = self.active_section
            target = "simple_next" if to == "next" else "simple_prev"
            self.active_section = getattr(self.active_section, target)
            if this_section.is_root and to == "next":
                self.active_section = this_section.first_child
            navigated = this_section is not self.active_section
            if navigated:
                self.go_to_first_of_section()
            return navigated

    def go_to_next(self) -> bool:
        """Try to navigate to the next page."""
        current = self.current_page
        with suppress(PaginationError):
            self.current_page = current + 1
        return current != self.current_page

    def go_to_prev(self) -> bool:
        """Try to navigate to the previous page."""
        current = self.current_page
        with suppress(PaginationError):
            self.current_page = current - 1
        return current != self.current_page

    def go_to_first_of_section(self, section: Section = None):
        section = section or self.active_section
        self.current_page = section.pager.first

    def go_to_last_of_section(self, section: Section = None):
        section = section or self.active_section
        self.current_page = section.pager.last

    def get_view_title(self, include_author=False):
        if config.conf["general"]["show_file_name_as_title"]:
            filename = os.path.split(self.document.filename)[-1]
            view_title = os.path.splitext(filename)[0]
        else:
            view_title = self.current_book.title
            if include_author and self.current_book.author:
                author = self.current_book.author
                # Translators: the title of the window when an e-book is open
                view_title = _("{title} — by {author}").format(
                    title=view_title, author=author
                )
        return view_title + f" - {app.display_name}"

    def _detect_ebook_format(self, ebook_path):
        return os.path.splitext(ebook_path)[-1].lstrip(".").lower()
