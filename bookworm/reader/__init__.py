# coding: utf-8

import os
import wx
from bookworm import app
from bookworm import config
from bookworm import database
from bookworm import speech
from bookworm import sounds
from bookworm.i18n import is_rtl
from bookworm.document_formats import (
    FitzDocument,
    FitzEPUBDocument,
    DocumentError,
    PaginationError,
)
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    reader_section_changed,
)
from bookworm.logger import logger
from .text_to_speech import TextToSpeechProvider


log = logger.getChild(__name__)


class EBookReader(TextToSpeechProvider):
    """The controller that glues together the
    document model and the view model .
    """

    __slots__ = [
        "supported_ebook_formats",
        "document",
        "view",
        "__state",
        "current_book",
        "tts",
    ]

    # A list of document classes
    # Each class supports a different file format
    document_classes = (FitzEPUBDocument, FitzDocument)

    def __init__(self, view):
        super().__init__()
        self.supported_ebook_formats = {
            cls.format: cls for cls in self.document_classes
        }
        self.view = view
        self.reset()

    def reset(self):
        self.document = None
        self.__state = {}

    def load(self, ebook_path):
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
        self.active_section = self.document.toc_tree
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
    def ready(self):
        return self.document is not None

    @property
    def active_section(self):
        return self.__state.get("active_section")

    @active_section.setter
    def active_section(self, value):
        if (value is None) or (value is self.active_section):
            return
        elif self.active_section is not None:
            self.active_section.pager.reset()
        _prev_page = None if self.active_section is None else self.current_page
        self.__state["active_section"] = value
        self.view.tocTreeSetSelection(value)
        page_number = value.pager.current
        if page_number != _prev_page:
            self.current_page = page_number
        speech.announce(value.title)
        reader_section_changed.send(self, active=value)

    @property
    def current_page(self):
        assert self.active_section is not None, "No active section."
        return self.active_section.pager.current

    @current_page.setter
    def current_page(self, value):
        assert self.active_section is not None, "No active section."
        if value is None:
            return
        elif value not in self.active_section.pager:
            raise ValueError(f"Page {value} is out of range for this section.")
        _prev = self.active_section.pager.current
        self.active_section.pager.set_current(value)
        self.view.set_content(self.get_page_content(value))
        if config.conf["general"]["play_pagination_sound"]:
            sounds.pagination.play_after()
        # Translators: the label of the page content text area
        cmsg = _("Page {page} | {chapter}").format(
            page=value + 1, chapter=self.active_section.title
        )
        # Translators: a message that is announced after navigating to a page
        smsg = _("Page {page} of {total}").format(
            page=value + 1, total=len(self.document)
        )
        self.view.SetStatusText(cmsg)
        speech.announce(smsg)
        reader_page_changed.send(self, current=value, prev=_prev)

    def go_to_page(self, page_number, pos=0):
        """Go to a page. Takes care of selecting appropriate section."""
        target_section = self.document.toc_tree
        for section in self.document.toc_tree.children:
            if page_number in section.pager:
                target_section = section
                break
        assert (
            page_number in target_section.pager
        ), f"Page {page_number} is out of range for this document."
        self.active_section = target_section
        self.current_page = page_number
        self.view.contentTextCtrl.SetInsertionPoint(pos)

    def get_page_content(self, page_number):
        if page_number not in self.document:
            raise PaginationError(
                f"Page {page_number} is out of range for this document."
            )
        page = self.document.get_page_content(page_number)
        return page

    def navigate(self, to, unit):
        assert to in ("next", "prev"), f"Invalid value {to} for arg`to`."
        assert unit in ("page", "section"), f"Invalid value {unit} for arg`unit`."
        if unit == "page":
            try:
                action_func = getattr(self.active_section.pager, f"go_to_{to}")
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

    def is_first_of_section(self, page_number):
        for sect in self.document.toc_tree:
            if page_number == sect.pager.first:
                return True
        return False

    def is_last_of_section(self, page_number):
        for sect in self.document.toc_tree:
            if page_number == sect.pager.last:
                return True
        return False

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
