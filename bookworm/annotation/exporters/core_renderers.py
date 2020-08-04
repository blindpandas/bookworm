# coding: utf-8

import os
import mistune
from bookworm.utils import escape_html
from .base_renderer import BaseRenderer


class PlainTextRenderer(BaseRenderer):
    """Renders items to a text document."""

    name = "text"
    # Translators: the name of a document file format
    display_name = _("Plain Text")
    output_ext = ".txt"

    def add_newline(self):
        self.output.write(os.linesep)

    def start_document(self):
        self.output.write(self.title)
        self.add_newline()
        self.output.write("=" * 30)
        self.add_newline()

    def end_document(self):
        self.add_newline()
        self.output.write("=" * 30)
        # Translators: written to the end of the plain-text file when exporting comments or highlights
        self.output.write(_("End of File"))
        self.add_newline()

    def start_section(self, title):
        self.output.write("~" * 30)
        self.add_newline()
        self.output.write(title)
        self.add_newline()
        self.output.write("~" * 30)
        self.add_newline()

    def end_section(self):
        self.add_newline()

    def render_item(self, item):
        self.output.write(f"{item.title} — " + _("Page {}").format(item.page_number))
        self.add_newline()
        self.output.write(item.content)
        self.add_newline()


class MarkdownRenderer(BaseRenderer):
    """Renders notes to a markdown document."""

    name = "markdown"
    # Translators: the name of a document file format
    display_name = _("Markdown")
    output_ext = ".md"

    def add_newline(self):
        self.output.write("\n")

    def start_document(self):
        # Translators: written to output file when exporting comments or highlights
        self.output.write("# " + _("Notes For {}").format(self.title))
        self.add_newline()

    def end_document(self):
        self.add_newline()

    def start_section(self, title):
        self.output.write(f"## {title}")
        self.add_newline()

    def end_section(self):
        self.add_newline()

    def render_item(self, item):
        # Translators: written to output file when exporting comments or highlights
        self.output.write(
            f"### {item.title} — " + _("**Page {}**").format(item.page_number)
        )
        self.output.write(item.content)
        self.add_newline()


class HTMLRenderer(MarkdownRenderer):
    """Renders notes to HTML."""

    name = "html"
    # Translators: the name of a document file format
    display_name = _("HTML")
    output_ext = ".html"

    def start_document(self):
        etitle = escape_html(self.title)
        # Translators: used as a title for an html file when exporting comments or highlights
        trans_title = _("Annotations — {}").format(etitle)
        head = (
            "<!doctype html>"
            "<html><head>"
            f"<title>{trans_title}</title>"
            "</head><body>"
            f"<h1>{trans_title}</h1>"
        )
        self.output.write(head)

    def end_document(self):
        self.output.write("</body></html>")

    def start_section(self, title):
        etitle = escape_html(title)
        self.output.write(f"<section><h2>{etitle}</h2>")

    def end_section(self):
        self.output.write("</section>")

    def render_item(self, item):
        etitle = escape_html(item.title)
        self.output.write(f"<article><header><h3>{etitle}</h3></header>")
        # Translators: page number as shown when exporting comments or highlights
        trans_page = _("Page {}").format(item.page_number)
        self.output.write(f"<aside>{trans_page}</aside>")
        for paragraph in item.content.splitlines():
            eparagraph = escape_html(paragraph)
            self.output.write(f"<p>{eparagraph}</p>")
        self.output.write(f"<footer>{trans_page}</footer></article>")
