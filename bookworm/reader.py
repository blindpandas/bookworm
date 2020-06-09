# coding: utf-8

import os
import wx
from bookworm import typehints as t
from bookworm import app
from bookworm import config
from bookworm import database
from bookworm import speech
from bookworm.resources import sounds
from bookworm.i18n import is_rtl
from bookworm.document_formats import (
    FitzDocument,
    FitzEPUBDocument,
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
    document_classes = (FitzEPUBDocument, FitzDocument)

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
            self.view.notify_user(
                # Translators: the title of a message shown
                # when the format of the e-book is not supported
                _("Unsupported Document Format"),
                # Translators: the content of a message shown
                # when the format of the e-book is not supported
                _("The format of the given document is not supported by Bookworm."),
                icon=wx.ICON_WARNING,
            )
            return
        document_cls = self.supported_ebook_formats[ebook_format]
        try:
            self.document = document_cls(filename=ebook_path)
            self.document.read()
        except DocumentError as e:
            self.view.notify_user(
                # Translators: the title of an error message
                _("Error Openning Document"),
                # Translators: the content of an error message
                _(
                    "Could not open file {file}\n."
                    "Either the file  has been damaged during download, "
                    "or it has been corrupted in some other way."
                ).format(file=ebook_path),
                icon=wx.ICON_ERROR,
            )
            log.exception(f"Error opening document.\r\n{e.args}", exc_info=True)
            self.reset()
            return
        self.current_book = self.document.metadata
        self.view.add_toc_tree(self.document.toc_tree)
        self.view.set_text_direction(is_rtl(self.document.language))
        self.current_page = 0
        self.view.SetTitle(self.get_view_title(include_author=True))
        last_position = database.get_last_position(ebook_path.lower())
        if last_position is not None:
            self.go_to_page(*last_position)
        reader_book_loaded.send(self)
        return True

    def unload(self):
        if self.ready:
            self.save_current_position()
            self.document.close()
            self.reset()
            reader_book_unloaded.send(self)

    def save_current_position(self):
        log.debug("Saving current position.")
        filename = self.document.filename
        # Some times we may need to shadow the original document with another
        #  one, for example when we decrypt it, or when we make it a11y friendly
        if getattr(self.document, "_original_file_name", None):
            filename = self.document._original_file_name
        database.save_last_position(
            filename.lower(),
            self.current_page,
            self.view.contentTextCtrl.InsertionPoint,
        )

    @property
    def ready(self) -> bool:
        return self.document is not None

    @property
    def active_section(self) -> Section:
        return self.__state.get("active_section")

    @active_section.setter
    def active_section(self, value: Section):
        if value is self.active_section:
            return
        self.__state["active_section"] = value
        self.view.tocTreeSetSelection(value)
        if self.current_page not in value.pager:
            self.current_page = value.pager.first
        speech.announce(value.title)
        reader_section_changed.send(self, active=value)

    @property
    def current_page(self) -> int:
        return self.__state["current_page_index"]

    @current_page.setter
    def current_page(self, value: int):
        if value not in self.document:
            raise PaginationError("Page out of range.")
        _prev = self.__state.setdefault("current_page_index", 0)
        self.__state["current_page_index"] = value
        page = self.document[value]
        if page.section is not self.active_section:
            self.active_section = page.section
        self.view.set_content(page.get_text())
        if config.conf["general"]["play_pagination_sound"]:
            sounds.pagination.play_after()
        # Translators: the label of the page content text area
        cmsg = _("Page {page} | {chapter}").format(
            page=page.number, chapter=page.section.title
        )
        # Translators: a message that is announced after navigating to a page
        smsg = _("Page {page} of {total}").format(
            page=page.number, total=len(self.document)
        )
        self.view.SetStatusText(cmsg)
        speech.announce(smsg)
        reader_page_changed.send(self, current=value, prev=_prev)

    @property
    def current_page_object(self) -> BasePage:
        """Return the current page."""
        return self.document[self.current_page]

    def go_to_page(self, page_number: int, pos: int=0):
        """Go to a page. Takes care of selecting appropriate section."""
        self.current_page = page_number
        self.view.contentTextCtrl.SetInsertionPoint(pos)

    def navigate(self, to: str, unit: str):
        assert to in ("next", "prev"), f"Invalid value {to} for arg`to`."
        assert unit in ("page", "section"), f"Invalid value {unit} for arg`unit`."
        if unit == "page":
            try:
                action_func = getattr(self, f"go_to_{to}")
                self.current_page = action_func()
                return True
            except PaginationError:
                return False
        elif unit == "section":
            this_section = self.active_section
            target = "simple_next" if to == "next" else "simple_prev"
            self.active_section = getattr(self.active_section, target)
            if this_section.is_root and to == "next":
                self.active_section = this_section.first_child
            return this_section is not self.active_section

    def go_to_next(self) -> int:
        """Try to navigate to the next page or raise PaginationError."""
        next_item = self.current_page + 1
        self.current_page = next_item

    def go_to_prev(self) -> int:
        """Try to navigate to the previous page or raise PaginationError."""
        prev_item = self.current_page - 1
        self.current_page = prev_item

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
