# coding: utf-8

from __future__ import annotations
import ftfy
from functools import cached_property, lru_cache
from pyxpdf import Document as XPdfDocument, Config as XPdfConfig
from pyxpdf.xpdf import TextOutput as XPdfTextOutput, TextControl as XPdfTextControl
from pyxpdf_data import generate_xpdfrc
from bookworm.paths import data_path
from bookworm.document_formats.base import ReadingMode, DocumentCapability as DC
from bookworm.logger import logger
from .fitz_document import FitzDocument, FitzPage

log = logger.getChild(__name__)
XPDF_CONFIG = dict(text_keep_tiny=False, text_eol="unix", text_page_breaks=False)
XPDF_READING_MODE_TO_BOOKWORM_READING_MODE = {
    ReadingMode.DEFAULT: "reading",
    ReadingMode.READING_ORDER: "simple",
    ReadingMode.PHYSICAL: "physical",
}


class FitzPdfPage(FitzPage):
    """Represents a page of a pdf document."""

    def __init__(self, *args, xpdf_text_output, **kwargs):
        super().__init__(*args, **kwargs)
        self.xpdf_text_output = xpdf_text_output

    def get_text(self):
        text = self.xpdf_text_output.get(self.index)[:-1]
        return self.normalize_text(text)

    def normalize_text(self, text):
        text = ftfy.fix_text(text, normalization="NFKC")
        return super().normalize_text(text)

    def get_label(self) -> str:
        return self._fitz_page.get_label().strip()


class FitzPdfDocument(FitzDocument):
    """Support for Pdf documents."""

    format = "pdf"
    # Translators: the name of a document file format
    name = _("Portable Document (PDF)")
    extensions = ("*.pdf",)
    capabilities = FitzDocument.capabilities | DC.PAGE_LABELS
    supported_reading_modes = (
        ReadingMode.DEFAULT,
        ReadingMode.READING_ORDER,
        ReadingMode.PHYSICAL,
    )

    @lru_cache(maxsize=1000)
    def get_page(self, index: int) -> FitzPage:
        return FitzPdfPage(self, index, xpdf_text_output=self.xpdf_text_output)

    @cached_property
    def xpdf_text_output(self):
        reading_mode = XPDF_READING_MODE_TO_BOOKWORM_READING_MODE[
            self.reading_options.reading_mode
        ]
        xtext_ctrl = XPdfTextControl(
            mode=reading_mode,
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
        is_ok = bool(self._ebook.authenticate(password))
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
