# coding: utf-8

import os
import mistune
from bookworm.utils import escape_html
from .base_renderer import BaseRenderer, TextRenderer


class PlainTextRenderer(TextRenderer):
    """Renders items to a text document."""

    name = "text"
    # Translators: written to output document when exporting a comment/highlight
    display_name = _("Plain Text")
    output_ext = ".txt"

    def add_newline(self):
        self.output.write(os.linesep)

    def start_document(self):
        if self.book is not None:
            self.output.write(self.book)
            self.add_newline()
        if self.section:
            self.output.write(_("Section: {}").format(self.section))
            self.add_newline()
        if self.tag:
            # Translators: written to output document when exporting files
            self.output.write(_("Tagged: {}").format(self.tag))
            self.add_newline()
        self.output.write("=" * 30)
        self.add_newline()

    def end_document(self):
        self.add_newline()
        self.output.write("=" * 30)
        self.add_newline()
        # Translators: written to the end of the plain-text file when exporting comments or highlights
        self.output.write(_("End of File"))

    def render_item(self, item):
        has_prev = False
        if self.options.include_book_title:
            self.output.write(item.book.title)
            has_prev = True
        if self.options.include_page_number:
            if has_prev:
                self.output.write(" — ")
            self.output.write(_("Page {}").format(item.page_number))
            has_prev = True
        if self.options.include_section_title:
            if has_prev:
                self.output.write(" — ")
            self.output.write(item.section_title)
            has_prev = True
        if has_prev:
            self.add_newline()
        self.output.write(item.content.strip())
        self.add_newline()
        if self.options.include_tags and item.tags:
            self.output.write(" ".join(f"#{tag}" for tag in item.tags))
            self.add_newline()
        self.add_newline()


class MarkdownRenderer(TextRenderer):
    """Renders notes to a markdown document."""

    name = "markdown"
    # Translators: the name of a document file format
    display_name = _("Markdown")
    output_ext = ".md"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__order = 0

    def add_newline(self):
        self.output.write("\n")

    def start_document(self):
        if self.book is not None:
            self.output.write(f"# {self.book}")
            self.add_newline()
        if self.section:
            self.output.write("## " + _("Section: {}").format(self.section))
            self.add_newline()
        if self.tag:
            self.output.write("## " + _("Tagged: {}").format(self.tag))
            self.add_newline()
        self.output.write("=" * 30)
        self.add_newline()

    def end_document(self):
        self.add_newline()

    def render_item(self, item):
        self.__order += 1
        self.output.write(f"## {self.__order}")
        self.add_newline()
        has_prev = False
        if self.options.include_book_title:
            self.output.write(f"**{item.book.title}**")
            has_prev = True
        if self.options.include_page_number:
            if has_prev:
                self.output.write(" — ")
            self.output.write(_("Page {}").format(item.page_number))
            has_prev = True
        if self.options.include_section_title:
            if has_prev:
                self.output.write(" — ")
            self.output.write(item.section_title)
            has_prev = True
        if has_prev:
            self.add_newline()
        self.output.write(item.content.strip())
        self.add_newline()
        if self.options.include_tags and item.tags:
            # Translators: written to output document when exporting a comment/highlight
            self.output.write(_("Tagged") + ": ")
            self.output.write(" ".join(tag for tag in item.tags))
            self.add_newline()
        self.add_newline()


class HTMLRenderer(MarkdownRenderer):
    """Renders notes to HTML."""

    name = "html"
    # Translators: the name of a document file format
    display_name = _("HTML")
    output_ext = ".html"

