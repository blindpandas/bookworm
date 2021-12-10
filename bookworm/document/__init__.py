# coding: utf-8

from .base import (
    BaseDocument,
    BasePage,
    SinglePageDocument,
    SinglePage,
    DummyDocument,
)
from .elements import (
    Section,
    Pager,
    LinkTarget,
    BookMetadata,
    TreeStackBuilder,
    SINGLE_PAGE_DOCUMENT_PAGER,
)
from .features import (
    DocumentCapability,
    ReadingMode,
    READING_MODE_LABELS,
)
from .exceptions import (
    DocumentError,
    ChangeDocument,
    DocumentIOError,
    DocumentEncryptedError,
    PaginationError,
)
from .formats import *


def create_document(uri, read=True):
    doc_cls = BaseDocument.get_document_class_given_format(uri.format.lower())
    if doc_cls is None:
        raise UnsupportedDocumentFormatError(f"Document Format {uri.format} is not supported.")
    document = doc_cls(uri)
    if read:
        document.read()
    return document
