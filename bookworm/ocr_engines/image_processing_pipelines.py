# coding: utf-8

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO
from PIL import Image, ImageOps
from bookworm import typehints as t
from bookworm.logger import logger


log = logger.getChild(__name__)


@dataclass
class ImageBlueprint:
    data: bytes
    width: int
    height: int

    @property
    def size(self):
        return (self.width, self.height)
    



@dataclass
class ImageProcessingPipeline(metaclass=ABCMeta):
    """Preprocesses images before running OCR."""
    images: t.Tuple[ImageBlueprint]
    ocr_request: "OcrRequest"
    args: dict = field(default_factory=dict)

    @abstractmethod
    def should_process(self) -> bool:
        """Should this pipeline be applied given the arguments."""

    @abstractmethod
    def process(self) -> t.Tuple["ImageBlueprint"]:
        """Do the actual processing of the given images."""



class ThresholdProcessingPipeline(ImageProcessingPipeline):
    """Binarize the given images using PIL."""

    DEFAULT_THRESHOLD = 220

    def should_process(self) -> bool:
        return True

    def process(self) -> t.Tuple["ImageBlueprint"]:
        threshold = self.args.get("threshold", self.DEFAULT_THRESHOLD)
        binarizer = lambda x : 255 if x > threshold else 0
        for image in self.images:
            img = Image.frombytes("RGBA", (image.width, image.height), image.data).convert("L")
            img = img.point(binarizer, mode='1').convert("RGBA")
            image.data = img.tobytes()
            yield image


class DPIProcessingPipeline(ImageProcessingPipeline):
    """Change the pixel dencity of the given images using PIL."""

    DPI_300_SIZE = 2048

    def should_process(self) -> bool:
        return True

    def _do_resize(self, image):
        img = Image.frombytes("RGBA", (image.width, image.height), image.data)
        w, h = image.size
        if 'scaling_factor' in self.args:
            factor = self.args['scaling_factor']
        else:
            factor = min(1, float(self.DPI_300_SIZE / w))
        nw, nh = int(factor * w), int(factor * h)
        image.data = img.resize(
            (nw, nh),
            resample=Image.BICUBIC
        ).tobytes()
        image.width, image.height = nw, nh
        return image

    def process(self) -> t.Tuple["ImageBlueprint"]:
        for image in self.images:
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


class InvertColourProcessingPipeline(ImageProcessingPipeline):
    """Invert the given images."""

    def should_process(self) -> bool:
        return True

    def process(self) -> t.Tuple["ImageBlueprint"]:
        for image in self.images:
            img = Image.frombytes("RGBA", (image.width, image.height), image.data)
            image.data = ImageOps.invert(img).convert("RGBA").tobytes()
            yield image

    
class RotationProcessingPipeline(ImageProcessingPipeline):
    """Rotates the given image."""

    ROTATION_METHODS = ("VERTICAL", "HORIZONTAL")
    ROTATION = ROTATION_METHODS[0]

    def should_process(self) -> bool:
        return self.ROTATION not in self.ROTATION_METHODS

    def process(self) -> t.Tuple["ImageBlueprint"]:
        for image in self.images:
            img = Image.frombytes("RGBA", (image.width, image.height), image.data)
            rotation = self.args.get("rotation", self.ROTATION)
            rotator = ImageOps.flip if rotation == "VERTICAL" else ImageOps.mirror
            image.data = rotator(img).convert("RGBA").tobytes()
            yield image
