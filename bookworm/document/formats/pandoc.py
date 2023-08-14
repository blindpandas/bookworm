# coding: utf-8

from __future__ import annotations

from functools import cache

from bookworm import pandoc
from bookworm.logger import logger

from .html import BaseHtmlDocument

log = logger.getChild(__name__)


class BasePandocDocument(BaseHtmlDocument):
    format = None
    name = None
    extensions = ()

    @classmethod
    def check(cls):
        return pandoc.is_pandoc_installed()

    @cache
    def get_html(self):
        return pandoc.convert(
            from_format=self.format,
            to_format="html",
            input_file=self.get_file_system_path(),
        ).decode("utf-8")


class RtfDocument(BasePandocDocument):
    """Rich Text document."""

    format = "rtf"
    # Translators: the name of a document file format
    name = _("Rich Text Document")
    extensions = ("*.rtf",)


class DocbookDocument(BasePandocDocument):
    """Docbook is a format for writing technical documentation. It uses it's own markup."""

    format = "docbook"
    # Translators: the name of a document file format
    name = _("Docbook Document")
    extensions = ("*.docbook",)


class JupyterNotebookDocument(BasePandocDocument):
    """Notebooks are used for data analysis and interactive code tutorials."""

    format = "ipynb"
    # Translators: the name of a document file format
    name = _("Jupyter notebook")
    extensions = ("*.ipynb",)


class LaTeXDocument(BasePandocDocument):
    """LaTeX is the de facto standard for the communication and publication of scientific documents."""

    format = "latex"
    # Translators: the name of a document file format
    name = _("LaTeX Document")
    extensions = ("*.tex",)


class Text2TagsDocument(BasePandocDocument):
    """A light markup language for representing HTML documents."""

    format = "t2t"
    # Translators: the name of a document file format
    name = _("Text2Tags Document")
    extensions = ("*.t2t",)


class ManPageDocument(BasePandocDocument):
    """a form of software documentation usually found on a Unix or Unix-like operating system."""

    format = "man"
    # Translators: the name of a document file format
    name = _("Unix manual page")
    extensions = list(f"*.{i}" for i in range(1, 9))
