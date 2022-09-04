# coding: utf-8

from __future__ import annotations

from bookworm import pandoc
from bookworm.document.uri import DocumentUri
from bookworm.logger import logger
from bookworm.paths import app_path, home_data_path
from .. import ChangeDocument
from .. import DocumentCapability as DC
from .html import BaseHtmlDocument

log = logger.getChild(__name__)


class RtfDocument(BaseHtmlDocument):

    format = "rtf"
    # Translators: the name of a document file format
    name = _("Rich Text Document")
    extensions = ("*.rtf",)

    @classmethod
    def check(cls):
        return pandoc.is_pandoc_installed()

    def read(self):
        self.__html_content = pandoc.convert(
            from_format="rtf",
            to_format="html",
            input_file=self.get_file_system_path()
        ).decode("utf-8")
        super().read()

    def get_html(self):
        return self.__html_content

    def parse_html(self):
        return self.parse_to_full_text()

