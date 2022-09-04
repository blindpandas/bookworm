# coding: utf-8

from __future__ import annotations
from functools import cache
from bookworm import pandoc
from bookworm.document.uri import DocumentUri
from bookworm.logger import logger

from .. import ChangeDocument
from .. import DocumentCapability as DC
from .. import DocumentEncryptedError, DocumentError, DummyDocument
from .fitz import FitzDocument
from .html import BaseHtmlDocument


log = logger.getChild(__name__)


class FitzFB2Document(FitzDocument):

    format = "fb2fitz"
    # Translators: the name of a document file format
    name = _("Fiction Book (FB2)")
    extensions = ("*.fb2",)

    @classmethod
    def check(cls):
        return not pandoc.is_pandoc_installed()


class FB2Document(BaseHtmlDocument):

    format = "fb2html"
    # Translators: the name of a document file format
    name = _("Fiction Book (FB2)")
    extensions = ("*.fb2",)

    @classmethod
    def check(cls):
        return pandoc.is_pandoc_installed()

    def parse_html(self):
        return self.parse_to_full_text()

    @cache
    def get_html(self):
        return pandoc.convert(
            from_format="fb2",
            to_format="html",
            input_file=self.get_file_system_path()
        ).decode("utf-8")
