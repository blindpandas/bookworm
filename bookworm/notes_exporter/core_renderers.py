# coding: utf-8

import mistune
from bookworm.utils import escape_html
from .base_renderer import BaseRenderer


class PlainTextRenderer(BaseRenderer):
    """Renders notes to a text document."""

    name = "text"
    display_name = "Plain Text "
    output_ext = ".txt"

    def start_document(self):
        self.output.write(f"Notes For {self.title}\n")
        self.output.write("=" * 30)
        self.output.write("\n\n")

    def end_document(self):
        self.output.write("\r\n\r\nEnd of File")

    def start_section(self, title):
        self.output.write("~" * 30)
        self.output.write(f"\n{title}\n")
        self.output.write("~" * 30)
        self.output.write("\n")

    def end_section(self):
        self.output.write("\n\n")

    def render_note(self, note):
        self.output.write(f"\n{note.title} — (Page {note.page_number})\n")
        self.output.write("\n")
        self.output.write(note.content)


class MarkdownRenderer(BaseRenderer):
    """Renders notes to a markdown document."""

    name = "markdown"
    display_name = "Markdown"
    output_ext = ".md"

    def start_document(self):
        self.output.write(f"# Notes For {self.title}\r\r\r")

    def end_document(self):
        pass

    def start_section(self, title):
        self.output.write(f"## {title}\r\r")

    def end_section(self):
        self.output.write("\r\r")

    def render_note(self, note):
        self.output.write(f"### {note.title} — **(Page {note.page_number})**\r\r")
        self.output.write(note.content)
        self.output.write("\r\r")


class HTMLRenderer(MarkdownRenderer):
    """Renders notes to HTML."""

    name = "html"
    display_name = "HTML"
    output_ext = ".html"

    def start_document(self):
        etitle = escape_html(self.title)
        head = (
            "<!doctype html>"
            "<html><head>"
            f"<title>Notes — {etitle}</title>"
            "</head><body>"
            f"<h1>Notes for {etitle}</h1>"
        )
        self.output.write(head)

    def end_document(self):
        self.output.write("</body></html>")

    def start_section(self, title):
        etitle = escape_html(title)
        self.output.write(f"<section><h2>{etitle}</h2>")

    def end_section(self):
        self.output.write("</section>")

    def render_note(self, note):
        etitle = escape_html(note.title)
        self.output.write(f"<article><header><h3>{etitle}</h3></header>")
        self.output.write(f"<aside>(Page {note.page_number})</aside>")
        for paragraph in note.content.splitlines():
            eparagraph = escape_html(paragraph)
            self.output.write(f"<p>{eparagraph}</p>")
        self.output.write("<footer>End of section</footer></article>")
