# coding: utf-8

import os
import wx
from bookworm import config
from bookworm import database
from bookworm import speech
from bookworm import sounds
from bookworm.document_formats import FitzDocument, FitzEPUBDocument, PaginationError
from bookworm.signals import (
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
    reader_section_changed,
)
from bookworm.logger import logger
from .tex_to_speech import TextToSpeechProvider


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
        self.document = None
        self.__state = {}

    def load(self, ebook_path):
        ebook_format = self._detect_ebook_format(ebook_path)
        if ebook_format not in self.supported_ebook_formats:
            raise IOError(f"Unsupported ebook format {ebook_format}.")
        document_cls = self.supported_ebook_formats[ebook_format]
        self.document = document_cls(filename=ebook_path)
        self.document.read()
        self.current_book = self.document.metadata
        self.view.add_toc_tree(self.document.toc_tree)
        self.active_section = self.document.toc_tree
        self.view.SetTitle(self.get_view_title())
        last_position = database.get_last_position(ebook_path.lower())
        if last_position is not None:
            self.go_to_page(*last_position)
        reader_book_loaded.send(self)

    def unload(self):
        if self.ready:
            self.save_current_position()
            self.document.close()
            self.document = None
            self.__state.clear()
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
        self.__state["active_section"] = value
        self.view.tocTreeSetSelection(value)
        self.current_page = value.pager.current
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
        self.view.SetStatusText(f"Page {value + 1} | {self.active_section.title}")
        speech.announce(f"Page {value + 1} of {len(self.document)}")
        reader_page_changed.send(self, current=value, prev=_prev)

    def go_to_page(self, page_number, pos=0):
        """Go to a page. Takes care of selecting appropriate section."""
        target_section = self.document.toc_tree
        for section in self.document.toc_tree.children:
            if page_number in section.pager:
                target_section = section
                break
        if page_number not in target_section.pager:
            raise PaginationError(
                f"Page {page_number} is out of range for this document."
            )
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
                view_title += f" — by {self.current_book.author}"
        return view_title

    def _detect_ebook_format(self, ebook_path):
        return os.path.splitext(ebook_path)[-1].lstrip(".").lower()

    def notify_user(self, title, message):
        wx.MessageBox(message, title, wx.ICON_INFORMATION)
