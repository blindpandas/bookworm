# coding: utf-8

from .base import SearchRequest, DocumentCapability, DocumentError, DocumentIOError, PaginationError
from .pdf_document import FitzPdfDocument
from .mupdf_document import FitzEPUBDocument, FitzFB2Document
from .plain_text_document import PlainTextDocument
from .html_document import HtmlDocument
