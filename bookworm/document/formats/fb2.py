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
from .pandoc import BasePandocDocument

log = logger.getChild(__name__)


class FitzFB2Document(FitzDocument):
    format = "fb2fitz"
    # Translators: the name of a document file format
    name = _("Fiction Book (FB2)")
    extensions = ("*.fb2",)

    @classmethod
    def check(cls):
        return not pandoc.is_pandoc_installed()


class FB2Document(BasePandocDocument):
    format = "fb2"
    # Translators: the name of a document file format
    name = _("Fiction Book (FB2)")
    extensions = ("*.fb2",)
