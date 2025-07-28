# coding: utf-8

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass, field
from io import StringIO
from operator import attrgetter
from typing import Callable
from more_itertools import first_true
import time

from bookworm import config
from bookworm import i18n
from bookworm import app
from bookworm import typehints as t
from bookworm.i18n import LocaleInfo
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from bookworm.utils import NEWLINE

from .image_processing_pipelines import ImageProcessingPipeline

log = logger.getChild(__name__)

# Default interval in seconds between concurrent API requests for rate-limited engines.
# 1.0 seconds provides a safe buffer for a 2 QPS limit.
DEFAULT_RATE_LIMIT_INTERVAL = 1.0

def _initialize_worker_process():
    """
    Initializes necessary subsystems for a worker process.
    This function is called at the beginning of a task that runs in a separate process
    to ensure that configurations is loaded correctly.
    """
    if config.conf is None:
        log.debug("Worker process: Initializing configuration.")
        config.setup_config()


@dataclass
class OcrRequest:
    languages: list[LocaleInfo]
    image: ImageIO
    image_processing_pipelines: t.Tuple[ImageProcessingPipeline] = field(
        default_factory=tuple
    )
    cookie: t.Optional[t.Any] = None
    engine_options: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.languages:
            raise ValueError(
                "At least one language should be provided for the OCR request to be valid."
            )

    @property
    def language(self):
        """Returns the primary language."""
        return self.languages[0]


@dataclass
class OcrResult:
    recognized_text: str
    ocr_request: OcrRequest

    @property
    def cookie(self):
        return self.ocr_request.cookie


class BaseOcrEngine(metaclass=ABCMeta):
    """An interface to all of  the ocr engines used in Bookworm."""

    name = None
    """The short name for this engine."""
    display_name = None
    """The user-facing name of this engine."""
    __supports_more_than_one_recognition_language__ = False
    """Does this engine supports more than one recognition language?"""

    # If True, a delay will be added between concurrent requests in scan_to_text.
    __requires_rate_limiting__ = False

    @classmethod
    @abstractmethod
    def check(cls) -> bool:
        """Check the availability of this engine at runtime."""

    @classmethod
    def get_engine_options(cls) -> list[EngineOption]:
        """
        Returns a list of configurable options for this engine.
        Subclasses should override this to expose their specific settings.
        """
        return []

    @classmethod
    @abstractmethod
    def get_recognition_languages(cls) -> t.List[LocaleInfo]:
        """Return a list of all the languages supported by this engine."""

    @classmethod
    def preprocess_and_recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        images = cls.preprocess_image(ocr_request)
        text = []
        for image in images:
            ocr_req = OcrRequest(
                image=image,
                languages=ocr_request.languages,
                engine_options=ocr_request.engine_options,
            )
            recog_result = cls.recognize(ocr_req)
            text.append(recog_result.recognized_text)
        return OcrResult(recognized_text="\n".join(text), ocr_request=ocr_request)

    @classmethod
    def preprocess_image(
        cls,
        ocr_request: OcrRequest,
    ) -> t.Iterable[ImageIO]:
        images = (ocr_request.image,)
        sorted_ipp = sorted(
            list(ocr_request.image_processing_pipelines),
            key=attrgetter("run_order"),
        )
        for pipeline_cls in sorted_ipp:
            pipeline = pipeline_cls(images, ocr_request)
            if pipeline.should_process():
                images = pipeline.process()
        return images

    @classmethod
    @abstractmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        """Perform the given ocr request and return the result."""

    @classmethod
    def scan_to_text(
        cls,
        doc: "BaseDocument",
        output_file: t.PathLike,
        ocr_options: "OcrOptions",
    ):
        _initialize_worker_process()
        if not cls.check():
            raise RuntimeError(f"OCR Engine {cls} is not available.")
        total = len(doc)
        out = StringIO()

        def recognize_page(page):
            """
            A helper function to recognize a single page and handle errors gracefully.
            This function runs in a worker thread from the ThreadPoolExecutor.
            """
            if cls.__requires_rate_limiting__:
                # Add a small delay to avoid hitting API rate limits.
                time.sleep(DEFAULT_RATE_LIMIT_INTERVAL)
            try:
                # Create a request for the current page
                ocr_req = OcrRequest(
                    languages=ocr_options.languages,
                    image=page.get_image(ocr_options.zoom_factor),
                    cookie=page.number,
                    # Pass through the engine options selected by the user
                    engine_options=ocr_options.engine_options,
                )
                # This call can raise OcrError for this specific page
                return cls.preprocess_and_recognize(ocr_req)
            except OcrError as e:
                # If any OCR error occurs for this page, log it and return None
                log.error(
                    f"Failed to recognize page {page.number}: {e}", exc_info=False
                )
                return None
            except Exception:
                # Catch any other unexpected errors for this page
                log.exception(
                    f"An unexpected error occurred while processing page {page.number}."
                )
                return None

        try:
            with ThreadPoolExecutor(4) as pool:
                for idx, res in enumerate(pool.map(recognize_page, doc)):
                    if res is None:
                        # The page failed to recognize, the error has been logged.
                        # We still yield the progress to update the progress bar.
                        yield idx
                        continue  # Skip to the next page

                    out.write(
                        f"Page {res.cookie}{NEWLINE}{res.recognized_text}{NEWLINE}\f{NEWLINE}"
                    )
                    yield idx  # Yield progress

            with open(output_file, "w", encoding="utf8") as file:
                file.write(out.getvalue())
        finally:
            out.close()
            doc.close()

    @classmethod
    def get_sorted_languages(cls):
        langs = cls.get_recognition_languages()
        current_lang = first_true(
            langs,
            pred=lambda lang: lang.should_be_considered_equal_to(app.current_language),
            default=None,
        )
        if current_lang is not None:
            langs.remove(current_lang)
            langs.insert(0, current_lang)
        return langs


@dataclass
class EngineOption:
    """Represents a configurable option for an OCR engine."""

    key: str  # The key used in the payload, e.g., "detect_direction"
    label: str  # The user-facing label for the checkbox
    default: bool = False  # Default state of the checkbox

    # A function that returns True if the option should be shown for a given engine
    is_supported: Callable[["BaseOcrEngine"], bool] = lambda engine: True


class OcrError(Exception):
    """Base exception for all OCR-related errors."""

    pass


class OcrAuthenticationError(OcrError):
    """Raised when API key or authentication fails."""

    pass


class OcrNetworkError(OcrError):
    """Raised for network-related issues during OCR."""

    pass


class OcrProcessingError(OcrError):
    """Raised when the OCR service returns a specific error for a request."""

    pass
