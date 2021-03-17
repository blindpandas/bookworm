# coding: utf-8

import numpy as np
import cv2
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO
from PIL import Image, ImageOps, ImageEnhance
from bookworm import typehints as t
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from . import cv2_utils


log = logger.getChild(__name__)


@dataclass
class ImageProcessingPipeline(metaclass=ABCMeta):
    """Preprocesses images before running OCR."""

    images: t.Tuple[ImageIO]
    ocr_request: "OcrRequest"
    args: dict = field(default_factory=dict)
    run_order: t.ClassVar[int] = 0

    @abstractmethod
    def should_process(self) -> bool:
        """Should this pipeline be applied given the arguments."""

    def process_image(self, image) -> ImageIO:
        """Process a single image."""
        return image

    def process(self) -> t.Tuple[ImageIO]:
        yield from (self.process_image(img) for img in self.images)


class TwoInOneScanProcessingPipeline(ImageProcessingPipeline):
    """Splits the given page into two pages and processes each page separately."""

    run_order = 10

    def should_process(self) -> bool:
        return True

    def process(self) -> t.Tuple[ImageIO]:
        for image in self.images:
            img = Image.frombytes("RGB", (image.width, image.height), image.data)
            w, h = image.width, image.height
            pg_left = img.crop((0, 0, w / 2, h))
            pg_right = img.crop((w / 2, 0, w, h))
            pages = (pg_left, pg_right)
            if self.ocr_request.language.is_rtl:
                pages = (pg_right, pg_left)
            for pg in pages:
                new_image = image.__class__(
                    data=pg.convert("RGB").tobytes(), width=pg.width, height=pg.height
                )
                yield new_image


class DPIProcessingPipeline(ImageProcessingPipeline):
    """Change the pixel dencity of the given images using PIL."""

    run_order = 20
    DPI_300_SIZE = 1024

    def should_process(self) -> bool:
        return True

    def _cv2_based_resizing(self, image):
        w, h = image.size
        factor = max(1, float(self.DPI_300_SIZE / w))
        nw, nh = int(factor * w), int(factor * h)
        cv2img = image.to_cv2()
        img = cv2.resize(cv2img, (nw, nh), cv2.INTER_CUBIC)
        return image.from_cv2(img)

    def process_image(self, image):
        img = image.to_pil()
        w, h = image.size
        if "scaling_factor" in self.args:
            factor = self.args["scaling_factor"]
        else:
            factor = max(1, float(self.DPI_300_SIZE / w))
        return ImageIO.from_pil(
            img.resize((int(factor * w), int(factor * h)), resample=Image.LANCZOS)
        )


class ThresholdProcessingPipeline(ImageProcessingPipeline):
    """Binarize the given images using opencv."""

    run_order = 30

    def should_process(self) -> bool:
        return True

    def process_image(self, image):
        img = image.to_cv2().astype(np.uint8)
        ret, th = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return ImageIO.from_cv2(th)


class DeskewProcessingPipeline(ImageProcessingPipeline):
    """Deskews the given image."""

    run_order = 40

    def should_process(self) -> bool:
        return True

    def process_image(self, image):
        img = image.to_cv2().astype(np.uint8)
        desk_img = cv2_utils.correct_skew(img)
        return ImageIO.from_cv2(desk_img)


class BlurProcessingPipeline(ImageProcessingPipeline):
    """Blurs the given image to remove noise."""

    run_order = 50

    def should_process(self) -> bool:
        return True

    def image_smoothening(self, img):
        blur = cv2.GaussianBlur(img, (1, 1), 0)
        return blur

    def process_image(self, image):
        img = image.to_cv2().astype(np.uint8)
        img = self.image_smoothening(img)
        return ImageIO.from_cv2(img)


class DilationProcessingPipeline(ImageProcessingPipeline):
    """Dilates the given image."""

    run_order = 60

    def should_process(self) -> bool:
        return True

    def process_image(self, image):
        img = image.to_cv2().astype(np.uint8)
        kernel = np.ones((5, 5), np.uint8)
        img = cv2.dilate(img, kernel, iterations=1)
        return ImageIO.from_cv2(img)


class ErosionProcessingPipeline(ImageProcessingPipeline):
    """Applys erosion to the given image."""

    run_order = 70

    def should_process(self) -> bool:
        return True

    def process_image(self, image):
        img = image.to_cv2().astype(np.uint8)
        kernel = np.ones((5, 5), np.uint8)
        img = cv2.erode(img, kernel, iterations=1)
        return ImageIO.from_cv2(img)


class ConcatImagesProcessingPipeline(ImageProcessingPipeline):
    """Concats the given images into one image."""

    run_order = 240

    def should_process(self) -> bool:
        return True  # len({img.size for img in self.images}) == 1

    def process(self) -> t.Iterable[ImageIO]:
        imagelist = []
        for img in self.images:
            imagelist.append(img.to_cv2())
            imagelist.append(np.zeros((25, img.width), dtype=np.uint8) + 255)
        w_min = min(im.shape[1] for im in imagelist)
        im_list_resize = [
            cv2.resize(
                im,
                (w_min, int(im.shape[0] * w_min / im.shape[1])),
                interpolation=cv2.INTER_CUBIC,
            )
            for im in imagelist
        ]
        img = cv2.vconcat(im_list_resize)
        yield ImageIO.from_cv2(img)


class DebugProcessingPipeline(ImageProcessingPipeline):
    """A pipeline that allows you to view the resulting image."""

    run_order = 250

    def should_process(self) -> bool:
        return True

    def process_image(self, image):
        image.to_pil().show()
        return image


class InvertColourProcessingPipeline(ImageProcessingPipeline):
    """Invert the given images."""

    def should_process(self) -> bool:
        return True

    def process_image(self, image):
        img = cv2.bitwise_not(image.to_cv2())
        return ImageIO.from_cv2(img)


class SharpenColourProcessingPipeline(ImageProcessingPipeline):
    """Sharpens the given images."""

    def should_process(self) -> bool:
        return True

    def process_image(self, image):
        img = ImageEnhance.Sharpness(image.to_pil()).enhance(2.0)
        return ImageIO.from_pil(img)


class RotationProcessingPipeline(ImageProcessingPipeline):
    """Rotates the given image."""

    ROTATION_METHODS = ("VERTICAL", "HORIZONTAL")
    ROTATION = ROTATION_METHODS[0]

    def should_process(self) -> bool:
        return self.ROTATION not in self.ROTATION_METHODS

    def process_image(self, image):
        img = Image.frombytes("RGB", (image.width, image.height), image.data)
        rotation = self.args.get("rotation", self.ROTATION)
        rotator = ImageOps.flip if rotation == "VERTICAL" else ImageOps.mirror
        image.data = rotator(img).convert("RGB").tobytes()
        return image


class DrainProcessingPipeline(ImageProcessingPipeline):
    """Discards images that fits a specific criteria."""

    def should_process(self) -> bool:
        return True

    def should_drop(self, image):
        """Should we drop this image."""
        return NotImplemented

    def process(self):
        for image in self.images:
            if self.should_drop(image):
                continue
            yield image


class EmptyPageDrainProcessingPipeline(DrainProcessingPipeline):
    """Drops empty (i.e. white) pages from this pipeline."""

    def should_drop(self, image):
        low, high = image.to_pil().convert("L").getextrema()
        return (high - low) <= 5
