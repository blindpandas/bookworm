# coding: utf-8

from __future__ import annotations

from functools import cache
from bookworm import pandoc
from bookworm.logger import logger

from .. import DocumentError
from .html import BaseHtmlDocument

log = logger.getChild(__name__)


class DocbookDocument(BaseHtmlDocument):
    """Docbook is a format for writing technical documentation. It uses it's own markup."""

    format = "docbook"
    # Translators: the name of a document file format
    name = _("Docbook Document")
    extensions = ("*.docbook",)

    @classmethod
    def check(cls):
        return pandoc.is_pandoc_installed()

    def parse_html(self):
        return self.parse_to_full_text()

    @cache
    def get_html(self):
        return pandoc.convert(
            from_format="docbook",
            to_format="html",
            input_file=self.get_file_system_path()
        ).decode("utf-8")