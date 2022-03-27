# coding: utf-8

"""Contains DocumentException and its derivatives."""

from bookworm.logger import logger

log = logger.getChild(__name__)


class DocumentError(Exception):
    """The base class of all document related exceptions."""


class ChangeDocument(Exception):
    """Change this document to another document."""

    def __init__(self, old_uri, new_uri, reason):
        self.old_uri = old_uri
        self.new_uri = new_uri
        self.reason = reason
        self.new_uri.fallback_uri = self.old_uri


class DocumentIOError(DocumentError, IOError):
    """Raised when the document could not be loaded."""


class DocumentEncryptedError(DocumentError):
    """Raised when the document is encrypted with an encryption key."""


class DocumentRestrictedError(DocumentError):
    """Raised when the document is restricted with a restriction technology (e.g. Digital Rights Management (DRM))."""


class PaginationError(DocumentError, IndexError):
    """Raised when the  `next` or `prev` page is not available."""


class UnsupportedDocumentFormatError(DocumentError):
    """Raised when the document format is not supported."""
