# coding: utf-8

import mistune
from bs4 import BeautifulSoup
from .base_renderer import BaseRenderer


class PlainTextRenderer(BaseRenderer):
    """Renders notes to a text document."""

    name = "text"
    display_name = "Plain Text "
    output_ext = ".txt"

    def start_document(self):
        self.output.append(f"Notes For {self.title}\n")
        self.output.append("=" * 30)
        self.output.append("\n\n")

    def end_document(self):
        self.output.append("\r\n\r\nEnd of File")

    def start_section(self, title):
        self.output.append("~" * 30)
        self.output.append(f"\n{title}\n")
        self.output.append("~" * 30)
        self.output.append("\n")

    def end_section(self):
        self.output.append("\n\n")

    def render_note(self, note):
        self.output.append(f"\n{note.title} — " f"(Page {note.page_number})\n")
        self.output.append("\n")
        self.output.append(note.content)


class MarkdownRenderer(BaseRenderer):
    """Renders notes to a markdown document."""

    name = "markdown"
    display_name = "Markdown"
    output_ext = ".md"

    def start_document(self):
        self.output.append(f"# Notes For {self.title}\r\r\r")

    def end_document(self):
        pass

    def start_section(self, title):
        self.output.append(f"## {title}\r\r")

    def end_section(self):
        self.output.append("\r\r")

    def render_note(self, note):
        self.output.append(f"### {note.title} — " f"**(Page {note.page_number})**\r\r")
        self.output.append(note.content)
        self.output.append("\r\r")


class HTMLRenderer(MarkdownRenderer):
    """Renders notes to HTML."""

    name = "html"
    display_name = "HTML"
    output_ext = ".html"

    def start_document(self):
        pass

    def render(self):
        content = super().render()
        content = f"<title>Book Notes, {self.title}</title>" + content
        content_healed = BeautifulSoup(mistune.markdown(content, escape=False), "lxml")
        return str(content_healed)
