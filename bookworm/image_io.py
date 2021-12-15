# coding: utf-8

from __future__ import annotations
import io
import tempfile
import wx
import fitz
from dataclasses import dataclass
from PIL import Image
from lazy_import import lazy_module
from bookworm import typehints as t
from bookworm.logger import logger

np = lazy_module("numpy")
cv2 = lazy_module("cv2")


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
        return cls.from_wx_image(wx_bitmap.ConvertToImage())

    @classmethod
    def from_wx_image(cls, wxImage):
        """
        Based on pyWiki 'Working With Images' @  http://wiki.wxpython.org/index.cgi/WorkingWithImages
        Credit: Ray Pasco      
        """
        keepTransp = createTransp = True
        # These can never be simultaneous.
        hasMask  = wxImage.HasMask()
        hasAlpha = wxImage.HasAlpha()
        # Always convert a mask into an aplha layer.
        # Deal with keeping or discarding this alpha later on.
        if hasMask :    # Is always mutually exclusive with hasAlpha.                
            wxImage.InitAlpha()     # Convert the separate mask to a 4th alpha layer.
            hasAlpha = True
        image_size = tuple(wxImage.GetSize())      # All images here have the same size.    
        # Create an RGB pilImage and stuff it with RGB data from the wxImage.
        pilImage = Image.new( 'RGB', image_size )
        pilImage.frombytes( bytes(wxImage.GetDataBuffer()))
        # May need the separated planes if an RGBA image is needed. later.
        r_pilImage, g_pilImage, b_pilImage = pilImage.split()        
        if hasAlpha and keepTransp:
            # Must recompose the pilImage from 4 layers.
            r_pilImage, g_pilImage, b_pilImage = pilImage.split()
            # Create a Black L pilImage and stuff it with the alpha data 
            #   extracted from the alpha layer of the wxImage.
            pilImage_L = Image.new( 'L', image_size )
            pilImage_L.frombytes( bytes(wxImage.GetAlphaBuffer()))
            # Create an RGBA PIL image from the 4 layers.
            pilImage = Image.merge( 'RGBA', (r_pilImage, g_pilImage, b_pilImage, pilImage_L) )
        elif (not hasAlpha) and createTransp :      # Ignore keepTransp - has no meaning
            # Create a Black L mode pilImage. The resulting image will still
            #  look the same, but will allow future transparency modification.
            pilImage_L = Image.new( 'L', image_size )        
            # Create an RGBA pil image from the 4 bands.
            pilImage = Image.merge( 'RGBA', (r_pilImage, g_pilImage, b_pilImage, pilImage_L) )
        return cls.from_pil(pilImage)

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

    def as_bytes(self, *, format="JPEG"):
        buf = io.BytesIO()
        self.to_pil().save(buf, format=format)
        return buf.getvalue()

    @classmethod
    def from_bytes(cls, value):
        img = Image.open(io.BytesIO(value))
        return cls.from_pil(img)
