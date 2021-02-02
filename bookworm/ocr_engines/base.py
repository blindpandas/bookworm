# coding: utf-8

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from contextlib import suppress
from chemical import it, ChemicalException
from bookworm import app
from bookworm.i18n import LocaleInfo
from bookworm import typehints as t
from bookworm.logger import logger


log = logger.getChild(__name__)


@dataclass
class OcrRequest:
    language: LocaleInfo
    imagedata: bytes
    width: int
    height: int
    cookie: t.Optional[t.Any] = None


@dataclass
class OcrResult:
    recognized_text: str
    cookie: t.Optional[t.Any]


class BaseOcrEngine(metaclass=ABCMeta):
    """An interface to all of  the ocr engines used in Bookworm."""

    name = None
    """The short name for this engine."""
    display_name = None
    """The user-facing name of this engine."""

    @classmethod
    @abstractmethod
    def check(cls) -> bool:
        """Check the availability of this engine at runtime."""

    @classmethod
    @abstractmethod
    def get_recognition_languages(cls) -> t.List[LocaleInfo]:
        """Return a list of all the languages supported by this engine."""

    @classmethod
    @abstractmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        """Perform the given ocr request and return the result."""

    @classmethod
    @abstractmethod
    def scan_to_text(
        cls,
        doc: "BaseDocument",
        lang: LocaleInfo,
        zoom_factor: float,
        should_enhance: bool,
        output_file: t.PathLike,
        channel: "QPChannel",
    ):
        """Scan the given document to text at once and update the progress."""

    @classmethod
    def get_sorted_languages(cls):
        langs = cls.get_recognition_languages()
        current_lang = None
        with suppress(ChemicalException):
            current_lang = it(langs).find(
                lambda lang: lang.should_be_considered_equal_to(app.current_language)
            )
        if current_lang is not None:
            langs.remove(current_lang)
            langs.insert(0, current_lang)
        return langs
