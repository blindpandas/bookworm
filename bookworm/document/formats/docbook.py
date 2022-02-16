# coding: utf-8

from __future__ import annotations
import contextlib
import string
import dateparser
import lxml
from functools import cached_property
from pathlib import Path
from more_itertools import zip_offset, first as get_first_element
from bookworm.i18n import LocaleInfo
from bookworm.structured_text import (
    TextRange,
    SemanticElementType,
    Style,
    HEADING_LEVELS,
)
from bookworm.utils import (
    remove_excess_blank_lines,
    NEWLINE,
)
from bookworm.logger import logger
from .. import (
    SinglePageDocument,
    Section,
    SINGLE_PAGE_DOCUMENT_PAGER,
    BookMetadata,
    DocumentCapability as DC,
    ReadingMode,
    DocumentError,
    DocumentIOError,
    TreeStackBuilder,
)


log = logger.getChild(__name__)



class DocbookDocument(SinglePageDocument):
    """Docbook is a format for writing technical documentation. It uses it's own markup."""

    format = "docbook"
    # Translators: the name of a document file format
    name = _("Docbook Document")
    extensions = ("*.docbook",)
    capabilities = (
        DC.TOC_TREE
        | DC.METADATA
        | DC.SINGLE_PAGE
        | DC.STRUCTURED_NAVIGATION
        | DC.TEXT_STYLE
        | DC.LINKS
        | DC.INTERNAL_ANCHORS
    )

    def read(self):
        super().read()
        self._text = None
        self._outline = None
        self._metainfo = None
        self._semantic_structure = {}
        self._style_info = {}
        with open(self.get_file_system_path(), "rb") as file:
            xml_content = file.read()
        self.xml_tree = lxml.etree.fromstring(xml_content)
        self.parse()

    def parse(self):
        self._metainfo = self._get_book_metadata()
        self._text = "".join(
            par
            for par in self.xml_tree.itertext(tag="para")
            if par.strip(string.whitespace)
        ).strip()
        #self._text = remove_excess_blank_lines(self._text)
        with self._create_toc_stack() as stack:
            pass

    @cached_property
    def language(self):
        if (lang_tag := self.xml_tree.attrib.get("lang")):
            try:
                return LocaleInfo(lang_tag)
            except ValueError:
                pass
        plane_text = "\n".join(self.xml_tree.itertext(tag="para"))
        return self.get_language(plane_text, is_html=False)

    def get_content(self):
        return self._text

    def get_document_semantic_structure(self):
        return self._semantic_structure

    def get_document_style_info(self):
        return self._style_info

    @cached_property
    def toc_tree(self):
        root = self._outline
        if len(root) == 1:
            return root[0]
        return root

    @cached_property
    def metadata(self):
        return self._metainfo

    @contextlib.contextmanager
    def _create_toc_stack(self):
        root = Section(
            pager=SINGLE_PAGE_DOCUMENT_PAGER,
            text_range=TextRange(0, -1),
            title=self._metainfo.title,
            level=1,
        )
        stack = TreeStackBuilder(root)
        yield stack, root
        self._outline = root

    def _get_book_metadata(self):
        xml_tree = self.xml_tree
        if not (title := xml_tree.xpath("/book/title//text()")):
            title = xml_tree.xpath("/book/bookinfo/title//text()")
        title = get_first_element(
            title,
            Path(self.get_file_system_path()).stem
        )
        author_firstname = get_first_element(
            xml_tree.xpath("/book/bookinfo/author/firstname//text()"),
            ""
        )
        author_surname = get_first_element(
            xml_tree.xpath("/book/bookinfo/author/surname//text()"),
            ""
        )
        author = " ".join([author_firstname, author_surname,])
        publisher = get_first_element(
            xml_tree.xpath("/book/bookinfo/corpname//text()"),
            ""
        )
        creation_date = xml_tree.xpath("/book/bookinfo/date//text()")
        if creation_date:
            parsed_date = dateparser.parse(
                creation_date[0],
                languages=[
                    self.language.two_letter_language_code,
                ]
            )
            creation_date = self.language.format_datetime(
                parsed_date, date_only=True, format="long", localized=True
            )
        return BookMetadata(
            title=title,
            author=author,
            creation_date=creation_date,
            publisher=publisher,
        )


