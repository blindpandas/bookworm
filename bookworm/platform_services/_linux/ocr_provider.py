# coding: utf-8


from bookworm import typehints as t

 
def is_ocr_available():
    return False

def get_recognition_languages():
    return []

def recognize(lang_tag: str, imagedata: bytes, width: int, height: int, cookie: t.Any = None):
    return ()


def scan_to_text(
    doc,
    lang: str,
    zoom_factor: float,
    should_enhance: bool,
    output_file: t.PathLike,
    channel: "QPChannel",):
    """Scan the given ebook to text file."""
