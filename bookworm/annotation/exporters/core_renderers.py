# coding: utf-8

import os
from bookworm.utils import escape_html
from .base_renderer import TextRenderer


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
            self.output.write(_("Section: {section_title}").format(section_title=self.section))
            self.add_newline()
        if self.tag:
            # Translators: written to output document when exporting files
            self.output.write(_("Tagged: {tag}").format(tag=self.tag))
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
            self.output.write(_("Page {number}").format(number=item.page_number))
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
        self._order = 0

    def add_newline(self):
        self.output.write("\n")

    def start_document(self):
        if self.book is not None:
            self.output.write(f"# {self.book}")
            self.add_newline()
        if self.section:
            self.output.write("## " + _("Section: {section_title}").format(section_title=self.section))
            self.add_newline()
        if self.tag:
            self.output.write("## " + _("Tagged: {tags}").format(tags=self.tag))
            self.add_newline()
        self.output.write("=" * 30)
        self.add_newline()

    def end_document(self):
        self.add_newline()

    def render_item(self, item):
        self._order += 1
        self.output.write(f"## {self._order}")
        self.add_newline()
        has_prev = False
        if self.options.include_book_title:
            self.output.write(f"**{item.book.title}**")
            has_prev = True
        if self.options.include_page_number:
            if has_prev:
                self.output.write(" — ")
            self.output.write(_("Page {number}").format(number=item.page_number))
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

    def start_document(self):
        title = {}
        if self.book is not None:
            title[_("Book")] = escape_html(self.book)
        if self.section:
            title[_("Section")] = escape_html(self.section)
        if self.tag:
            title[_("Tag")] = escape_html("# " + self.tag)
        html_title = " — ".join(t.strip() for t in title.values() if t.strip())
        self.output.write(
            "<!doctype html>\n"
            "<html>\n<head>\n"
            '<meta charset="UTF-8">\n'
            f"<title>{html_title}</title>\n"
            "</head>\n<body>\n"
        )
        self.output.write("<h1>" + _("Exported Annotations") + "</h1>\n")
        for label, value in title.items():
            self.output.write(f"<h2>{label}: {value}</h2>\n")

    def end_document(self):
        self.output.write(
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/clipboard.js/2.0.6/clipboard.min.js"></script>\n'
            '<script>new ClipboardJS("button");</script>\n'
            "</body>\n</html>"
        )

    def render_item(self, item):
        self._order += 1
        # Translators: label for a aria region containing annotation
        # used when exporting annotations to HTML
        self.output.write('<section aria-label="{}">\n'.format(_("Annotation")))
        self.output.write(f"<h3>{self._order}</h3>\n")
        self.output.write("<p>")
        if self.options.include_book_title:
            self.output.write(f"<span>{item.book.title}</span> ")
        if self.options.include_page_number:
            self.output.write(
                "<span>{}: {}</span> ".format(_("Page"), item.page_number + 1)
            )
        if self.options.include_section_title:
            self.output.write(f"<span>{item.section_title}</span> ")
        self.output.write("</p>")
        self.add_newline()
        # Translators: label of a button to copy the annotation to the clipboard
        # used when exporting annotations to HTML
        copy_clip_text = _("Copy to clipboard")
        element_id = f"annotationtext{self._order}"
        self.output.write(
            f'<button data-clipboard-target="#{element_id}" '
            f'aria-label="{copy_clip_text}">'
            "&#x1f4cb"
            "</button>\n"
        )
        self.output.write(
            f'<p><article><blockquote id="{element_id}">\n'
            f"{item.content.strip()}\n"
            "</blockquote></article></p>\n"
        )
        if self.options.include_tags and item.tags:
            # Translators: written to output document when exporting a comment/highlight
            tag_str = _("Tags")
            self.output.write("<p>" f'<aside aria-label="{tag_str}">')
            for tag in item.tags:
                self.output.write(f"<span># {tag}</span>")
            self.output.write("</p>" "</aside>")
            self.add_newline()
        self.output.write("<hr /></section>")
