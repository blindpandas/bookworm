# coding: utf-8

from __future__ import annotations

from datetime import datetime
from functools import cached_property, lru_cache

import ftfy
import regex
from dateutil.tz import tzoffset, tzutc
from pyxpdf import Config as XPdfConfig
from pyxpdf import Document as XPdfDocument
from pyxpdf.xpdf import TextControl as XPdfTextControl
from pyxpdf.xpdf import TextOutput as XPdfTextOutput
from pyxpdf_data import generate_xpdfrc

from bookworm.logger import logger
from bookworm.paths import data_path
from bookworm.utils import format_datetime

from .. import DocumentCapability as DC
from .. import ReadingMode
from .fitz import FitzDocument, FitzPage

log = logger.getChild(__name__)
XPDF_CONFIG = dict(text_keep_tiny=False, text_eol="unix", text_page_breaks=False)
BOOKWORM_READING_MODE_TO_XPDF_READING_MODE = {
    ReadingMode.DEFAULT: "reading",
    ReadingMode.READING_ORDER: "simple",
    ReadingMode.PHYSICAL: "physical",
}
# All of the parsing code is obtained from:
# https://stackoverflow.com/a/26796646
PDF_DATE_PATTERN = regex.compile(
    r"(D:)?"
    r"(?P<year>\d\d\d\d)"
    r"(?P<month>\d\d)"
    r"(?P<day>\d\d)"
    r"(?P<hour>\d\d)"
    r"(?P<minute>\d\d)"
    r"(?P<second>\d\d)"
    r"(?P<tz_offset>[+-zZ])?"
    r"(?P<tz_hour>\d\d)?"
    r"'?(?P<tz_minute>\d\d)?'?"
)


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
        reading_mode = BOOKWORM_READING_MODE_TO_XPDF_READING_MODE[
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
        self._pdf_fileobj = open(self.filename, "rb")
        self.xpdf_doc = XPdfDocument(self._pdf_fileobj, userpass=password)

    def read(self, filetype=None):
        super().read()
        if not self.is_encrypted():
            self.create_xpdf_document()

    def close(self):
        super().close()
        self._pdf_fileobj.close()

    @cached_property
    def metadata(self):
        meta = super().metadata
        if pub_year := meta.publication_year:
            try:
                parsed_creation_date = self.language.format_datetime(
                    self._parse_pdf_creation_date(pub_year),
                    format="medium",
                    localized=True,
                    date_only=False,
                )
            except:
                log.exception("Failed to parse pdf creation date", exc_info=True)
            else:
                meta.creation_date = parsed_creation_date
                meta.publication_year = ""
        return meta

    def decrypt(self, password):
        is_ok = bool(self._ebook.authenticate(password))
        if is_ok:
            self.create_xpdf_document(password=password)
        return is_ok

    @staticmethod
    def _parse_pdf_creation_date(date_str: str) -> datetime:
        match = PDF_DATE_PATTERN.match(date_str)
        if match:
            date_info = match.groupdict()
            for k, v in date_info.items():
                if v is None:
                    pass
                elif k == "tz_offset":
                    date_info[k] = v.lower()
                else:
                    date_info[k] = int(v)

            if date_info["tz_offset"] in ("z", None):
                date_info["tzinfo"] = tzutc()
            else:
                multiplier = 1 if date_info["tz_offset"] == "+" else -1
                date_info["tzinfo"] = tzoffset(
                    None,
                    multiplier
                    * (3600 * date_info["tz_hour"] + 60 * date_info["tz_minute"]),
                )

            for k in ("tz_offset", "tz_hour", "tz_minute"):
                del date_info[k]

            return datetime(**date_info)

    @staticmethod
    def get_xpdf_config_file():
        xpdf_config = data_path("xpdf_config", "default.xpdf")
        if not xpdf_config.exists():
            xpdf_config.parent.mkdir(parents=True, exist_ok=True)
            xpdf_config.write_text(generate_xpdfrc())
        return xpdf_config
