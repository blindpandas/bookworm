# coding: utf-8

import ftfy
from functools import cached_property
from pyxpdf import Document as XPdfDocument, Config as XPdfConfig
from pyxpdf.xpdf import TextOutput as XPdfTextOutput, TextControl as XPdfTextControl
from pyxpdf_data import generate_xpdfrc
from bookworm.paths import data_path
from bookworm.logger import logger
from .mupdf_document import FitzDocument, FitzPage

log = logger.getChild(__name__)
XPDF_CONFIG = dict(
    text_keep_tiny=False,
    text_eol='unix',
    text_page_breaks=False
)


class FitzPdfPage(FitzPage):
    """Represents a page of a pdf document."""

    def __init__(self, *args, xpdf_text_output, **kwargs):
        super().__init__(*args, **kwargs)
        self.xpdf_text_output = xpdf_text_output

    def get_text(self):
        text = self.xpdf_text_output.get(self.index)[:-1]
        return ftfy.fix_text(text, normalization="NFKC")


class FitzPdfDocument(FitzDocument):
    """Support for Pdf documents."""

    format = "pdf"
    # Translators: the name of a document file format
    name = _("Portable Document (PDF)")
    extensions = ("*.pdf",)

    def get_page(self, index: int) -> FitzPage:
        return FitzPdfPage(self, index, xpdf_text_output=self.xpdf_text_output)

    @cached_property
    def xpdf_text_output(self):
        xtext_ctrl = XPdfTextControl(
            mode="reading",
            enable_html=True,
            discard_diagonal=True,
        )
        return XPdfTextOutput(self.xpdf_doc, xtext_ctrl)

    def create_xpdf_document(self, password=None):
        cfg_file_path = str(self.get_xpdf_config_file())
        XPdfConfig.load_file(cfg_file_path)
        for cfg, val in XPDF_CONFIG.items():
            setattr(XPdfConfig, cfg, val)
        self.xpdf_doc = XPdfDocument(self.filename, userpass=password)

    def read(self, filetype=None):
        super().read()
        if not self.is_encrypted():
            self.create_xpdf_document()

    def close(self):
        super().close()

    def decrypt(self, password):
        is_ok =  bool(self._ebook.authenticate(password))
        if is_ok:
            self.create_xpdf_document(password=password)
        return is_ok

    @staticmethod
    def get_xpdf_config_file():
        xpdf_config = data_path("xpdf_config", "default.xpdf")
        if not xpdf_config.exists():
            xpdf_config.parent.mkdir(parents=True, exist_ok=True)
            xpdf_config.write_text(generate_xpdfrc())
        return xpdf_config

