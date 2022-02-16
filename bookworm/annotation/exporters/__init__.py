# coding: utf-8

from dataclasses import dataclass

from bookworm.logger import logger

from .core_renderers import HTMLRenderer, MarkdownRenderer, PlainTextRenderer

log = logger.getChild(__name__)

renderers = [PlainTextRenderer, HTMLRenderer, MarkdownRenderer]


@dataclass
class ExportOptions:
    output_file: str
    include_book_title: bool = True
    include_section_title: bool = True
    include_page_number: bool = True
    include_tags: bool = True
