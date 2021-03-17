# coding: utf-8

import io
import wx
import numpy as np
import cv2
import fitz
from dataclasses import dataclass
from PIL import Image
from bookworm import typehints as t
from bookworm.logger import logger


log = logger.getChild(__name__)


@dataclass
class ImageIO:
    """
    Represents an image which can be loaded/exported efficiently from and to
    several in-memory representations including PIL, cv2, and plain numpy arrays.
    """

    data: bytes
    width: int
    height: int
    mode: str = "RGB"

    def __repr__(self):
        return f"<ImageBlueprint: width={self.width}, height={self.height}, mode={self.mode}>"

    def __array__(self):
        return self.to_cv2()

    @property
    def size(self):
        return (self.width, self.height)

    def as_rgba(self):
        if self.mode == "RGBA":
            return self
        return self.from_pil(self.to_pil().convert("RGBA"))

    def as_rgb(self):
        if self.mode == "RGB":
            return self
        return self.from_pil(self.to_pil().convert("RGB"))

    def invert(self):
        return self.from_cv2(cv2.bitwise_not(self.to_cv2()))

    @classmethod
    def from_path(cls, image_path: t.PathLike) -> "ImageBlueprint":
        try:
            pil_image = Image.open(image_path).convert("RGB")
            return cls.from_pil(pil_image)
        except Exception:
            log.exception(
                f"Failed to load image from file '{image_path}'", exc_info=True
            )

    @classmethod
    def from_pil(cls, image: Image.Image) -> "ImageBlueprint":
        return cls(
            data=image.tobytes(),
            width=image.width,
            height=image.height,
            mode=image.mode,
        )

    @classmethod
    def from_cv2(cls, cv2_image):
        rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_GRAY2RGB)
        pil_image = Image.fromarray(np.asarray(rgb_image, dtype=np.uint8), mode="RGB")
        return cls.from_pil(pil_image)

    @classmethod
    def from_wx_bitmap(cls, wx_bitmap):
        raise NotImplementedError

    @classmethod
    def from_fitz_pixmap(cls, pixmap):
        return cls(
            data=pixmap.samples, width=pixmap.width, height=pixmap.height, mode="RGB"
        )

    def to_pil(self) -> Image.Image:
        return Image.frombytes("RGB", self.size, self.data)

    def to_cv2(self):
        pil_image = self.to_pil().convert("RGB")
        return cv2.cvtColor(np.array(pil_image, dtype=np.uint8), cv2.COLOR_RGB2GRAY)

    def to_wx_bitmap(self):
        img = self.as_rgb()
        return wx.ImageFromBuffer(
            img.width, img.height, bytearray(img.data)
        ).ConvertToBitmap()

    def to_fitz_pixmap(self):
        buf = io.BytesIO()
        self.to_pil().save(buf, format="png")
        return fitz.Pixmap(buf)
