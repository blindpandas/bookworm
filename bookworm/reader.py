# coding: utf-8

import os
import string
from contextlib import suppress
from pathlib import Path

from selectolax.parser import HTMLParser

from bookworm import app, config
from bookworm import typehints as t
from bookworm.commandline_handler import run_subcommand_in_a_new_process
from bookworm.database import DocumentPositionInfo
from bookworm.document import (
    ArchiveContainsMultipleDocuments,
    ArchiveContainsNoDocumentsError,
    BaseDocument,
    BasePage,
    ChangeDocument,
)
from bookworm.document import DocumentCapability as DC
from bookworm.document import (
    DocumentEncryptedError,
    DocumentError,
    DocumentIOError,
    PaginationError,
    Section,
)
from bookworm.document.formats import *
from bookworm.document.uri import DocumentUri
from bookworm.i18n import is_rtl
from bookworm.logger import logger
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    reader_section_changed,
    reading_position_change,
)
from bookworm.structured_text import SemanticElementType, TextStructureMetadata

log = logger.getChild(__name__)

PASS_THROUGH__DOCUMENT_EXCEPTIONS = {
    ArchiveContainsNoDocumentsError,
    ArchiveContainsMultipleDocuments,
}


def get_document_format_info():
    return BaseDocument.document_classes


class ReaderError(Exception):
    """Base class for all reader exceptions."""


class ResourceDoesNotExist(ReaderError):
    """The file does not exist."""


class UnsupportedDocumentError(ReaderError):
    """File type/format is not supported."""


class DecryptionRequired(Exception):
    """Raised to signal to the view that the document requires a password to be decrypted ."""


class UriResolver:
    """Retrieves a document given a uri."""

    def __init__(self, uri, num_fallbacks=0, original_uri=None):
        if isinstance(uri, str):
            try:
                self.uri = DocumentUri.from_uri_string(uri)
            except ValueError as e:
                raise ReaderError(f"Failed to parse document uri {self.uri}") from e
        else:
            self.uri = uri
        self.num_fallbacks = num_fallbacks
        self.original_uri = original_uri or self.uri
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
        try:
            doc = self._do_read_document()
            return doc, self.original_uri
        except ChangeDocument as e:
            # Propagate the original URI through the conversion chain.
            return UriResolver(uri=e.new_uri, original_uri=self.original_uri).read_document()
        except:
            if (fallback_uri := self.uri.fallback_uri) is not None:
                if self.num_fallbacks < 4:
                    return UriResolver(
                        uri=fallback_uri, num_fallbacks=self.num_fallbacks + 1, original_uri=self.original_uri
                    ).read_document()
            raise

    def _do_read_document(self):
        document = self.document_cls(self.uri)
        try:
            document.read()
        except DocumentEncryptedError:
            raise DecryptionRequired
        except DocumentIOError as e:
            raise ResourceDoesNotExist("Failed to load document") from e
        except Exception as e:
            if type(e) in PASS_THROUGH__DOCUMENT_EXCEPTIONS or isinstance(e, ChangeDocument):
                raise e
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

    def set_document(self, document, original_uri=None):
        self.document = document
        self.current_book = self.document.metadata
        self.__state.setdefault("current_page_index", -1)
        self.set_view_parameters()
        self.current_page = 0
        
        # Use the original URI for storage, falling back to the document's URI
        # if no original URI was passed (i.e., for non-converted files).
        uri_for_storage = original_uri or self.document.uri

        # Crucially, overwrite the document's current URI with the original one.
        # This ensures all subsequent operations (recents, pinning, position saving)
        # use the correct identifier for the file the user actually opened.
        self.document.uri = uri_for_storage

        if self.document.uri.view_args.get("save_last_position", True):
            log.debug("Retrieving last saved reading position from the database")
            self.stored_document_info = DocumentPositionInfo.get_or_create(
                title=self.current_book.title, uri=uri_for_storage
            )
        if open_args := self.document.uri.openner_args:
            page = int(open_args.get("page", 0))
            pos = int(open_args.get("position", 0))
            self.go_to_page(page, pos)
            self.view.contentTextCtrl.SetFocus()
        elif (
            self.stored_document_info
            and config.conf["general"]["open_with_last_position"]
        ):
            try:
                log.debug("Navigating to the last saved position.")
                page_number, pos = self.stored_document_info.get_last_position()
                self.go_to_page(page_number, pos)
            except:
                log.exception(
                    "Failed to restore last saved reading position", exc_info=True
                )
        if self.active_section is None:
            self.__state.setdefault(
                "active_section",
                self.document.get_section_at_position(self.view.get_insertion_point()),
            )
        reader_book_loaded.send(self)

    def set_view_parameters(self):
        self.view.set_title(self.get_view_title(include_author=True))
        self.view.set_text_direction(self.document.language.is_rtl)
        self.view.add_toc_tree(self.document.toc_tree)

    def load(self, uri: DocumentUri):
        document, original_uri = UriResolver(uri).read_document()
        self.set_document(document, original_uri=original_uri)

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
        if not self.document.is_single_page_document():
            self.active_section = page.section
        self.view.set_state_on_page_change(page)
        # if config.conf["appearance"]["apply_text_styles"] and DC.TEXT_STYLE in self.document.capabilities:
        # self.view.apply_text_styles(page.get_style_info())
        reader_page_changed.send(self, current=page, prev=None)

    def get_current_page_object(self) -> BasePage:
        """Return the current page."""
        return self.document.get_page(self.current_page)

    def go_to_page(
        self, page_number: int, pos: int = 0, set_focus_to_text_ctrl: bool = True
    ) -> bool:
        self.current_page = page_number
        self.view.set_insertion_point(pos, set_focus_to_text_ctrl)

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

    def perform_wormhole_navigation(
        self, *, page, start, end, last_position: tuple[int, int] = None
    ):
        """Jump to a certain location in the open document storing the current position in the navigation history."""
        this_page = self.current_page
        if last_position is None:
            last_position = (self.view.get_insertion_point(), None)
        if page is not None:
            self.go_to_page(page)
        self.view.go_to_position(start, end)
        reading_position_change.send(self.view, position=start, tts_speech_prefix="")
        self.push_navigation_stack(this_page, *last_position)

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

    @property
    def navigation_stack(self):
        return self.__state.setdefault("navigation_stack", [])

    def push_navigation_stack(self, last_page, last_pos_start, last_pos_end):
        self.navigation_stack.append(
            {
                "last_page": last_page,
                "source_range": (last_pos_start, last_pos_end),
            }
        )

    def pop_navigation_stack(self):
        try:
            nav_stack_top = self.navigation_stack.pop()
        except IndexError:
            self.view.notify_invalid_action()
            return
        else:
            if page_num := nav_stack_top.get("last_page"):
                self.go_to_page(page_num)
            start, end = nav_stack_top["source_range"]
            self.view.go_to_position(start, end)
            reading_position_change.send(
                self.view, position=start, tts_speech_prefix=""
            )

    def handle_special_action_for_position(self, position: int) -> bool:
        log.debug(f"Executing special action in position: {position}")
        for link_range in self.iter_semantic_ranges_for_elements_of_type(
            SemanticElementType.LINK
        ):
            if position in range(*link_range):
                self.navigate_to_link_by_range(link_range)
        try:
            for idx, tbl_range in enumerate(
                self.iter_semantic_ranges_for_elements_of_type(
                    SemanticElementType.TABLE
                )
            ):
                if position in range(*tbl_range):
                    table_markup = self.get_current_page_object().get_table_markup(idx)
                    self._show_table(table_markup)
        except NotImplementedError:
            pass

    @staticmethod
    def _get_semantic_element_from_page(page, element_type, forward, anchor):
        semantics = TextStructureMetadata(page.semantic_structure)
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

    def iter_semantic_ranges_for_elements_of_type(self, element_type):
        semantics = TextStructureMetadata(
            self.get_current_page_object().semantic_structure
        )
        yield from semantics.iter_ranges(element_type)

    def navigate_to_link_by_range(self, link_range):
        target_info = self.get_current_page_object().get_link_for_text_range(link_range)
        if target_info is None:
            log.warning(f"Could not resolve link target: {link_range=}")
            return
        elif target_info.is_external:
            self.view.go_to_webpage(target_info.url)
        else:
            start, end = target_info.position
            self.perform_wormhole_navigation(
                page=target_info.page, start=start, end=None, last_position=link_range
            )

    def get_view_title(self, include_author=False):
        if config.conf["general"]["show_file_name_as_title"]:
            try:
                document_path = self.document.get_file_system_path()
            except DocumentIOError:
                view_title = self.current_book.title
            else:
                filename = os.path.split(document_path)[-1]
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

    @staticmethod
    def open_document_in_a_new_instance(uri):
        run_subcommand_in_a_new_process(
            [
                "launcher",
                uri.base64_encode(),
            ],
            hidden=False,
        )

    def _show_table(self, table_markup):
        # Translators: title of a message dialog that shows a table as html document
        title = _("Table View")
        if (table_caption := HTMLParser(table_markup).css_first("caption")) is not None:
            caption_text = (
                table_caption.text().strip(string.whitespace).replace("\n", " ")
            )
            title = f"{caption_text} · {title}"
        self.view.show_html_dialog(table_markup, title=title)
