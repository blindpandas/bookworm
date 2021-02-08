# coding: utf-8

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from io import StringIO
from operator import attrgetter
from contextlib import suppress
from concurrent.futures import ThreadPoolExecutor
from chemical import it, ChemicalException
from bookworm import typehints as t
from bookworm import app
from bookworm.i18n import LocaleInfo
from bookworm.utils import NEWLINE
from bookworm.logger import logger
from .image_processing_pipelines import ImageBlueprint, ImageProcessingPipeline


log = logger.getChild(__name__)


@dataclass
class OcrRequest:
    language: LocaleInfo
    image: ImageBlueprint
    image_processing_pipelines: t.Tuple[ImageProcessingPipeline] = field(default_factory=tuple)
    cookie: t.Optional[t.Any] = None


@dataclass
class OcrResult:
    recognized_text: str
    cookie: t.Optional[t.Any] = None


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
    def preprocess_and_recognize(
        cls,ocr_request: OcrRequest) -> OcrResult:
        images = cls.preprocess_image(ocr_request)
        text = []
        for image in images:
            ocr_req = OcrRequest(
                image=image,
                language=ocr_request.language,
            )
            recog_result = cls.recognize(ocr_req)
            text.append(recog_result.recognized_text)
        return OcrResult(
            recognized_text="\n".join(text),
            cookie=ocr_request.cookie
        )

    @classmethod
    def preprocess_image(cls,ocr_request: OcrRequest,) -> t.Iterable[ImageBlueprint]:
        images = (ocr_request.image,)
        sorted_ipp = sorted(
            ocr_request.image_processing_pipelines,
            key=attrgetter("run_order")
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
        channel: "QPChannel",
    ):
        cls.check()
        total = len(doc)
        out = StringIO()

        def recognize_page(page):
            imagedata, width, height = page.get_image(ocr_options.zoom_factor)
            image = ImageBlueprint(
                data=imagedata,
                width=width,
                height=height
            )
            ocr_req = OcrRequest(
                language=ocr_options.language,
                image=image,
                cookie=page.number
            )
            return cls.preprocess_and_recognize(ocr_req)

        with ThreadPoolExecutor(4) as pool:
            for (idx, res) in enumerate(pool.map(recognize_page, doc)):
                out.write(f"Page {res.cookie}{NEWLINE}{res.recognized_text}{NEWLINE}\f{NEWLINE}")
                channel.push(idx)
        with open(output_file, "w", encoding="utf8") as file:
            file.write(out.getvalue())
        out.close()
        doc.close()
        channel.close()


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
