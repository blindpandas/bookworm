# coding: utf-8

from enum import IntEnum, auto


class ErrorCodes(IntEnum):
    unsupported_operation = auto()
    file_error = auto()
    unknown_error = auto()


class DocumentError(Exception):
    """The base class of all bookworm exceptions."""

    def __init__(self, error_code, message):
        self.error_code = error_code
        self.message = message


class DocumentReadError(DocumentError):
    """Raised when trying to open a document that could not be red."""
