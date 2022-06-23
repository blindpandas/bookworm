# coding: utf-8

from __future__ import annotations
import lxml
from mistune import markdown
from bookworm.utils import TextContentDecoder
from bookworm.logger import logger
from .html import BaseHtmlDocument


log = logger.getChild(__name__)


class MarkdownDocument(BaseHtmlDocument):

    format = "markdown"
    # Translators: the name of a document file format
    name = _("Markdown File")
    extensions = ("*.md",)

    def get_html(self):
        md_content = TextContentDecoder.from_filename(self.filename).get_utf8()
        rendered_markdown = markdown(md_content, escape=False)
        html_tree = lxml.html.fromstring(rendered_markdown)
        if not (doc_title := html_tree.xpath("(/html/body/h1)[1]//text()")):
            doc_title = self.filename.stem
        return "\n".join(
            [
                "<!doctype html>",
                "<html>",
                "<head>",
                '<meta charset="utf-8">',
                f"<title>{doc_title}</title>",
                "</head>",
                "<body>",
                rendered_markdown,
                "</body>",
                "</html>",
            ]
        )

    def read(self):
        self.filename = self.get_file_system_path()
        super().read()

    def parse_html(self):
        return self.parse_to_full_text()
