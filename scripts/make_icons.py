# coding: utf-8

"""Embed images in a python module for easier handling."""

import wx
import tempfile
from wx.tools.img2py import img2py
from pathlib import Path

_ = wx.App()

TARGET_SIZE = (24, 24)
IMAGE_SOURCE_FOLDER = "fullsize_images"
PY_MODULE = Path("bookworm/resources/images.py")


def convert_images():
    if PY_MODULE.exists():
        PY_MODULE.unlink()
    with tempfile.TemporaryDirectory() as temp:
        for index, imgfile in enumerate(Path(IMAGE_SOURCE_FOLDER).iterdir()):
            if imgfile.suffix != ".png":
                continue
            fname = Path(temp) / imgfile.name
            imageObj = wx.Image(str(imgfile))
            imageObj.Rescale(*TARGET_SIZE)
            imageObj.SaveFile(str(fname), wx.BITMAP_TYPE_PNG)
            print(f"Converting image: {imgfile.name}")
            append = bool(index)
            img2py(
                python_file=str(PY_MODULE),
                image_file=str(fname),
                append=append,
                compressed=True,
            )
        print("*" * 10 + " Done " + "*" * 10)


if __name__ == "__main__":
    convert_images()
