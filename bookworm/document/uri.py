# coding: utf-8

from __future__ import annotations
import base64
from pathlib import Path
from yarl import URL
from bookworm import typehints as t
from bookworm.document.base import BaseDocument
from bookworm.document.exceptions import UnsupportedDocumentFormatError
from bookworm.logger import logger


log = logger.getChild(__name__)
BOOKWORM_URI_SCHEME = "bkw"


class DocumentUri:
    __slots__ = [
        "format",
        "path",
        "openner_args",
        "view_args",
    ]

    def __init__(
        self,
        format: str,
        path: str,
        openner_args: dict[str, t.Union[str, int]],
        view_args: t.optional[dict[t.Any, t.Any]] = None,
    ):
        self.format = format
        self.path = path
        self.openner_args = openner_args
        self.view_args = view_args or {}

    @classmethod
    def from_uri_string(cls, uri_string):
        """Return a populated instance of this class or raise ValueError."""
        invalid_uri_string_exception = ValueError(f"Invalid uri string {uri_string}")
        try:
            uri = URL(uri_string)
        except:
            raise invalid_uri_string_exception
        if uri.scheme != BOOKWORM_URI_SCHEME:
            raise invalid_uri_string_exception
        return cls(
            format=uri.authority,
            path=uri.path.strip("/"),
            openner_args=dict(uri.query),
        )

    @classmethod
    def from_filename(cls, filename):
        filepath = Path(filename)
        if (doc_format := cls.get_format_by_filename(filepath)) is None:
            raise UnsupportedDocumentFormatError(
                f"Unsupported document format for file {filename}"
            )
        return cls(format=doc_format, path=str(filepath), openner_args={})

    @classmethod
    def is_bookworm_uri(cls, uri_string: str) -> bool:
        try:
            cls.from_uri_string(uri_string)
            return True
        except ValueError:
            return False

    def to_uri_string(self):
        return str(
            URL.build(
                scheme=BOOKWORM_URI_SCHEME,
                authority=self.format,
                path=str(self.path),
                query=self.openner_args,
            )
        )

    def to_bare_uri_string(self):
        return str(
            URL.build(
                scheme=BOOKWORM_URI_SCHEME,
                authority=self.format,
                path=f"/{str(self.path)}",
            )
        )

    def create_copy(self, format=None, path=None, openner_args=None, view_args=None):
        return DocumentUri(
            format=format or self.format,
            path=path or self.path,
            openner_args=self.openner_args | (openner_args or {}),
            view_args=self.view_args | (view_args or {}),
        )

    def base64_encode(self):
        return base64.urlsafe_b64encode(self.to_uri_string().encode("utf-8"))

    @classmethod
    def from_base64_encoded_string(cls, s):
        if isinstance(s, str):
            s = s.encode("utf-8")
        return cls.from_uri_string(base64.urlsafe_b64decode(s).decode("utf-8"))

    @classmethod
    def get_format_by_filename(cls, filename):
        """Get the document format using its filename."""
        fileext = Path(filename).suffix.strip(".").lower()
        if file_format := cls._get_format_given_extension(f"*.{fileext}"):
            return file_format
        possible_exts = tuple(str(filename).split("."))
        for idx in range(len(possible_exts) - 1):
            fileext = ".".join(possible_exts[idx:])
            if file_format := cls._get_format_given_extension(f"*.{fileext}"):
                return file_format

    @classmethod
    def _get_format_given_extension(cls, ext):
        for (doc_format, doc_cls) in BaseDocument.document_classes.items():
            if (doc_cls.extensions is not None) and (ext in doc_cls.extensions):
                return doc_format

    def is_equal_without_openner_args(self, other):
        return self.to_bare_uri_string() == other.to_bare_uri_string()

    def __hash__(self):
        return hash(self.to_uri_string())

    def __str__(self):
        return self.to_uri_string()

    def __repr__(self):
        return f"DocumentUri(format='{self.format}', path='{self.path}', openner_args={self.openner_args})"

    def __eq__(self, other):
        if not isinstance(other, DocumentUri):
            return NotImplemented
        return self.to_uri_string() == other.to_uri_string()
