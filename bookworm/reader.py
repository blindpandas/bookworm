# coding: utf-8

import os
from contextlib import suppress
from dataclasses import dataclass
from bookworm import typehints as t
from bookworm import app
from bookworm import config
from bookworm.database import DocumentPositionInfo
from bookworm.i18n import is_rtl
from bookworm.document_uri import DocumentUri
from bookworm.documents import (
    BaseDocument,
    ChangeDocument,
    DocumentCapability as DC,
    DocumentError,
    DocumentIOError,
    PaginationError,
)
from bookworm.documents.base import Section, BasePage
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    reader_section_changed,
)
from bookworm.structured_text import TextStructureMetadata
from bookworm.logger import logger


log = logger.getChild(__name__)


def get_document_format_info():
    return {cls.format: cls for cls in BaseDocument.document_classes}


class ReaderError(Exception):
    """Base class for all reader exceptions."""


class ResourceDoesNotExist(ReaderError):
    """The file does not exist."""


class UnsupportedDocumentError(ReaderError):
    """File type/format is not supported."""


class UriResolver:
    """Retrieves a document given a uri."""

    def __init__(self, uri):
        if isinstance(uri, str):
            try:
                self.uri = DocumentUri.from_uri_string(uri)
            except ValueError as e:
                raise ReaderError(f"Failed to parse document uri {self.uri}") from e
        else:
            self.uri = uri
        doc_format_info = get_document_format_info()
        if (doc_format := self.uri.format) not in doc_format_info:
            raise UnsupportedDocumentError(
                f"Could not open document from uri {self.uri}. The format is not supported."
            )
        self.document_cls = doc_format_info[doc_format]

    def __repr__(self):
        return f"UriResolver(uri={self.uri})"

    def should_read_async(self):
        return self.document_cls.should_read_async()

    def read_document(self):
        document = self.document_cls(self.uri)
        try:
            document.read()
        except DocumentIOError as e:
            raise ResourceDoesNotExist("Failed to load document") from e
        except ChangeDocument as e:
            log.debug(
                f"Changing document from {e.old_uri} to {e.new_uri}. Reason {e.reason}"
            )
            return UriResolver(uri=e.new_uri).read_document()
        except Exception as e:
            raise ReaderError("Failed to open document") from e
        return document


class EBookReader:
    """The controller that glues together the
    document model and the view model.
    """

    __slots__ = [
        "document",
        "stored_document_info",
        "view",
        "__state",
        "current_book",
    ]

    # Convenience method: make this available for importers as a staticmethod
    get_document_format_info = staticmethod(get_document_format_info)

    def __init__(self, view):
        self.view = view
        self.reset()

    def reset(self):
        self.document = None
        self.stored_document_info = None
        self.__state = {}

    def set_document(self, document):
        if not self.decrypt_document(document):
            return
        self.document = document
        self.current_book = self.document.metadata
        self.stored_document_info = DocumentPositionInfo.get_or_create(
            title=self.current_book.title, uri=self.document.uri
        )
        self.set_view_parameters()
        reader_book_loaded.send(self)

    def set_view_parameters(self):
        self.view.set_title(self.get_view_title(include_author=True))
        self.view.set_text_direction(self.document.language.is_rtl)
        self.view.add_toc_tree(self.document.toc_tree)
        self.__state.setdefault("current_page_index", -1)
        self.current_page = 0
        if config.conf["general"]["open_with_last_position"]:
            try:
                log.debug("Retrieving last saved reading position from the database")
                log.debug("Navigating to the last saved position.")
                page_number, pos = self.stored_document_info.get_last_position()
                self.go_to_page(page_number, pos)
            except:
                log.exception(
                    "Failed to restore last saved reading position", exc_info=True
                )

    def decrypt_document(self, document):
        return bool(self.view.try_decrypt_document(document))

    def load(self, uri: DocumentUri):
        document = UriResolver(uri).read_document()
        self.set_document(document)

    def unload(self):
        if self.ready:
            try:
                log.debug("Saving current position.")
                self.save_current_position()
                log.debug("Closing current document.")
                self.document.close()
            except:
                log.exception(
                    "An exception was raised while closing the eBook", exc_info=True
                )
                if app.debug:
                    raise
            finally:
                self.reset()
                reader_book_unloaded.send(self)

    def save_current_position(self):
        if self.stored_document_info is None:
            return
        self.stored_document_info.save_position(
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
        if self.document.has_toc_tree():
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
        # if config.conf["appearance"]["apply_text_styles"] and DC.TEXT_STYLE in self.document.capabilities:
        # self.view.apply_text_styles(page.get_style_info())
        reader_page_changed.send(self, current=page, prev=None)

    def get_current_page_object(self) -> BasePage:
        """Return the current page."""
        return self.document.get_page(self.current_page)

    def go_to_page(self, page_number: int, pos: int = 0) -> bool:
        self.current_page = page_number
        self.view.set_insertion_point(pos)

    def go_to_page_by_label(self, page_label):
        try:
            page = self.document.get_page_number_from_page_label(page_label)
            self.go_to_page(page.index)
            return True
        except LookupError:
            return False

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

    @staticmethod
    def _get_semantic_element_from_page(page, element_type, forward, anchor):
        semantics = TextStructureMetadata(page.get_semantic_structure())
        pos_getter = (
            semantics.get_next_element_pos
            if forward
            else semantics.get_prev_element_pos
        )
        return pos_getter(element_type, anchor=anchor)

    def get_semantic_element(self, element_type, forward, anchor):
        return self._get_semantic_element_from_page(
            self.get_current_page_object(), element_type, forward, anchor
        )

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
