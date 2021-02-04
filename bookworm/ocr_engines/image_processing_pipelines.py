# coding: utf-8

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from PIL import Image, ImageOps
from bookworm import typehints as t
from bookworm.logger import logger


log = logger.getChild(__name__)


@dataclass
class ImageProcessingPipeline(metaclass=ABCMeta):
    """Preprocesses images before running OCR."""
    images: t.Tuple["ImageBlueprint"]
    ocr_request: "OcrRequest"

    @abstractmethod
    def should_process(self) -> bool:
        """Should this pipeline be applied given the arguments."""

    @abstractmethod
    def process(self) -> t.Tuple["ImageBlueprint"]:
        """Do the actual processing of the given images."""



class ThresholdProcessingPipeline(ImageProcessingPipeline):
    """Binarize the given images using PIL."""

    THRESHOLD = 175

    def should_process(self) -> bool:
        return True

    def process(self) -> t.Tuple["ImageBlueprint"]:
        binarizer = lambda x : 255 if x > self.THRESHOLD else 0
        for image in self.images:
            img = Image.frombytes("RGBA", (image.width, image.height), image.data).convert("L")
            img = img.point(binarizer, mode='1').convert("RGBA")
            image.data = img.tobytes()
            yield image


class DPIProcessingPipeline(ImageProcessingPipeline):
    """Resize the given images using PIL."""

    SCALING_FACTOR = 4
    MAX_WIDTH = 1024
    MAX_HEIGHT = 2048

    def should_process(self) -> bool:
        return True

    def _do_resize(self, image):
        img = Image.frombytes("RGBA", (image.width, image.height), image.data)
        nw, nh = image.width * self.SCALING_FACTOR, image.height * self.SCALING_FACTOR
        image.data = img.resize(
            (nw, nh),
            resample=Image.BICUBIC,
        ).tobytes()
        image.width, image.height = nw, nh
        return image

    def process(self) -> t.Tuple["ImageBlueprint"]:
        for image in self.images:
            if image.width > self.MAX_WIDTH or image.height > self.MAX_HEIGHT:
                yield image
            else:
                yield self._do_resize(image)


class TwoInOneScanProcessingPipeline(ImageProcessingPipeline):
    """Splits the given page into two pages and processes each page separately."""

    def should_process(self) -> bool:
        return True

    def process(self) -> t.Tuple["ImageBlueprint"]:
        for image in self.images:
            img = Image.frombytes("RGBA", (image.width, image.height), image.data)
            w, h = image.width, image.height
            pg_left = img.crop((0, 0, w/2, h)) 
            pg_right = img.crop((w/2, 0, w, h)) 
            pages = (pg_right, pg_left)
            if self.ocr_request.language.is_rtl:
                pages = (pg_left, pg_right)
            for pg in pages:
                new_image = image.__class__(
                    data=pg.convert("RGBA").tobytes(),
                    width=pg.width,
                    height=pg.height
                )
                yield new_image