# coding: utf-8

from __future__ import annotations
import copy
import ebooklib
import more_itertools
from functools import cached_property, lru_cache
from hashlib import md5
from zipfile import ZipFile
from tempfile import TemporaryDirectory
from pathlib import Path, PurePosixPath
from urllib import parse as urllib_parse
from chemical import it
from ebooklib.epub import read_epub
from bs4 import BeautifulSoup
from bookworm.paths import home_data_path
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
from bookworm.utils import recursively_iterdir, is_external_url
from bookworm.logger import logger
from .. import (
    BaseDocument,
    BasePage,
    Section,
    LinkTarget,
    BookMetadata,
    Pager,
    DocumentCapability as DC,
    ReadingMode,
    TreeStackBuilder,
    ChangeDocument,
    DocumentError,
    DocumentEncryptedError,
)
from .fitz import FitzPage, FitzDocument


log = logger.getChild(__name__)


EMPTY_HTML_DOCUMENT = (
    "<!DOCTYPE html>\n"
    "<html>\n"
    "<head></head>\n"
    "<body></body>\n"
    "</html>"
)

class EpubPage(BasePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        section_ref = self.section.data["href"]
        html = self._get_html_with_href(section_ref)
        try:
            self._parse_and_extract_text_info(html)
        except ValueError:
            log.exception("Failed to parse text from html", exc_info=True)
            self._parse_and_extract_text_info("<html></html>")
        if "#" in section_ref and not self.extracted_text.strip():
            filename, html_id = section_ref.split("#")
            self._parse_and_extract_text_info(self.document._split_section_content[filename][""])

    def _parse_and_extract_text_info(self, html):
        structure_extractor = StructuredHtmlParser.from_string(html)
        self.extracted_text = structure_extractor.get_text()
        self.semantic_elements = structure_extractor.semantic_elements
        self.style_info = structure_extractor.styled_elements
        self.link_targets = structure_extractor.link_targets
        self.anchors = structure_extractor.anchors

    def get_text(self):
        return self.extracted_text

    def get_style_info(self) -> dict:
        return self.style_info

    def get_semantic_structure(self) -> dict:
        return self.semantic_elements

    def get_image(self, zoom_factor):
        raise NotImplementedError

    def resolve_link(self, link_range):
        if (target := self.link_targets.get(link_range)):
            if is_external_url(target):
                return LinkTarget(
                    url=target,
                    is_external=True
                )
            filename, anchor = (
                (target, None)
                if "#" not in target
                else target.split("#")
            )
            filename = urllib_parse.unquote(filename)
            target_section = self.document._filename_to_section.get(filename)
            if target_section is None:
                for (file, sect) in self.document._filename_to_section.items():
                    if file.endswith(filename):
                        target_section = sect
                        break
            if target_section is not None:
                target_page = self.document[target_section.pager.first]
                target_position = target_page.anchors.get(anchor, 0)
                return LinkTarget(
                    url=target,
                    is_external=False,
                    page=target_page.index,
                    position=target_position
                )




    def _get_proper_filename(self, href):
        members = self.document._filelist
        if href in members:
            return href
        for filename in members:
            if filename.endswith(href):
                return filename

    def parse_split_chapter(self, href):
        filename = self._get_proper_filename(href.split("#")[0])
        split_anchors = self.document._split_section_anchor_ids[filename]
        self.document._split_section_content[filename] = {}
        chapter_content = self.document.ziparchive.read(filename).decode("utf-8")
        soup = BeautifulSoup(chapter_content, "lxml")
        for this_anchor in reversed(split_anchors):
            this_tag = soup.find(attrs={"id": lambda x: x == this_anchor})
            markup_split = str(soup).split(str(this_tag))
            soup = BeautifulSoup(markup_split[0], "lxml")
            # If the tag is None, it probably means the content is overlapping
            # Skipping the insert is the way forward
            if this_tag:
                this_markup = BeautifulSoup(
                    str(this_tag).strip() + markup_split[1], "lxml"
                )
                self.document._split_section_content[filename][this_anchor] = str(
                    this_markup
                )
        # Remaining markup is assigned here
        self.document._split_section_content[filename][""] = str(soup)

    def _get_split_section_text(self, href):
        splitdata = href.split("#")
        if len(splitdata) == 2:
            filename, html_id = splitdata
        else:
            filename = splitdata[0]
            html_id = ""
        if (anchor_info := self.document._split_section_content.get(filename)) :
            try:
                return anchor_info[html_id]
            except KeyError:
                log.warning(
                    f"Could not get content for {html_id=} from parsed {filename=} with {href=}"
                )
                return ""
        if self._get_proper_filename(filename) is not None:
            self.parse_split_chapter(href)
            return self._get_split_section_text(href)
        else:
            return ""

    def _get_html_with_href(self, href):
        retval_html = None
        if (filename := self._get_proper_filename(href)) :
            if href not in self.document._split_section_anchor_ids:
                retval_html = self.document.ziparchive.read(filename).decode("utf-8")
            else:
                retval_html = self._get_split_section_text(href)
        elif (filename is None) and ("#" in href):
            retval_html = self._get_split_section_text(href)
        if retval_html is None:
            log.warning(
                f"Could not extract text from section with href: {href} and filename: {filename}"
            )
            retval_html = EMPTY_HTML_DOCUMENT
        retval_soup = BeautifulSoup(retval_html, "lxml")
        for file in self.section.data.get('additional_html_files', ()):
            html_content = self.document.ziparchive.read(file).decode("utf-8")
            for elm in BeautifulSoup(html_content, 'lxml'):
                retval_soup.body.append(copy.copy(elm))
        return str(retval_soup)


class EpubDocument(BaseDocument):

    format = "epub"
    # Translators: the name of a document file format
    name = _("Electronic Publication (EPUB)")
    extensions = ("*.epub",)
    capabilities = DC.TOC_TREE | DC.METADATA | DC.STRUCTURED_NAVIGATION | DC.TEXT_STYLE | DC.LINKS | DC.INTERNAL_ANCHORS
    default_reading_mode = ReadingMode.CHAPTER_BASED

    def __len__(self):
        return self.toc_tree.pager.last + 1

    @lru_cache(maxsize=1000)
    def get_page(self, index):
        return EpubPage(self, index)

    def read(self):
        self.fitz_doc = FitzEPUBDocument(self.uri)
        self.fitz_doc.read()
        self.filename = self.fitz_doc.filename
        self.epub = read_epub(self.filename)
        self.ziparchive = ZipFile(self.filename, "r")
        self._filelist = set(self.ziparchive.namelist())
        self._split_section_anchor_ids = {}
        self._split_section_content = {}
        # For the purposes of resolving internal anchors
        self._filename_to_section = {}
        super().read()

    def close(self):
        super().close()
        self.fitz_doc.close()
        self.ziparchive.close()

    @cached_property
    def language(self):
        return self.fitz_doc.language

    @cached_property
    def toc_tree(self):
        toc = self.fitz_doc._ebook.get_toc(simple=False)
        sect_count = len(toc)
        root = Section(
            title=self.metadata.title,
            pager=Pager(first=0, last=sect_count - 1),
            level=1,
        )
        stack = TreeStackBuilder(root)
        all_html_files = self.get_html_file_list()
        for (idx, (level, title, __, data)) in enumerate(toc):
            href = data["name"]
            section = stack.push(
                Section(
                    title=title,
                    pager=Pager(first=idx, last=idx),
                    level=level + 1,
                    data=dict(href=href),
                )
            )
            # ----------------
            filename, html_id = (
                (href, None)
                if "#" not in href
                else href.split("#")
            )
            self._filename_to_section[filename] = section
            # ----------------
            if html_id is not None:
                self._split_section_anchor_ids.setdefault(filename, []).append(html_id)
            # ----------------
            section_filename = (
                href if "#" not in href
                else href.split("#")[0]
            ).strip()
            if section_filename not in all_html_files:
                continue
            all_html_files[all_html_files.index(section_filename)] = section
            # End loop
        additional_html_files = (
            (sect, html_files)
            for (sect, *html_files)
            in more_itertools.split_before(all_html_files, pred=lambda item: isinstance(item, Section))
            if html_files and isinstance(sect, Section)
        )
        for (sect, additional_html_file_list) in additional_html_files:
            sect.data['additional_html_files'] = additional_html_file_list
            for aditional_file in additional_html_file_list:
                self._filename_to_section[aditional_file] = sect
        # ------------
        if sect_count == 0:
            href = (
                it(self.epub.items)
                .find(lambda item: "html" in item.media_type)
                .file_name
            )
            stack.push(
                Section(
                    title=_("Book contents"),
                    pager=Pager(first=0, last=0),
                    level=2,
                    data=dict(href=href),
                )
            )
            object.__setattr__(root.pager, "last", 0)
        return root

    @cached_property
    def metadata(self):
        return self.fitz_doc.metadata

    def get_cover_image(self):
        return self.fitz_doc.get_cover_image()

    def get_html_file_list(self):
        return [
            h.get_name().strip()
            for h in self.epub.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        ]


class FitzEPUBDocument(FitzDocument):

    __internal__ = True

    def read(self):
        try:
            super().read()
        except DocumentEncryptedError:
            log.debug("Got an encrypted file, will try to decrypt it...")
            raise ChangeDocument(
                old_uri=self.uri,
                new_uri=self.uri.create_copy(format="drm_epub"),
                reason="Document is encrypted with DRM",
            )


class _DrmFitzEpubDocument(EpubDocument):
    """Fixes DRM encrypted epub documents."""

    __internal__ = True
    format = "drm_epub"

    def read(self):
        self._original_filename = self.get_file_system_path()
        try:
            self.filename = self.make_unrestricted_file(self._original_filename)
            self.uri = self.uri.create_copy(
                path=self.filename,
            )
            super().read()
        except Exception as e:
            raise DocumentError("Could not open DRM encrypted epub document") from e

    @staticmethod
    def make_unrestricted_file(filename):
        """
        Try to remove Digital Rights Management (DRM) type
        encryption from the EPUB document.

        Legal note:
        The removal of the encryption from the file does not involve any
        violation of any laws whatsoever, as long as the user has obtained
        the eBook using legitimate means, and the user intents to use the
        content in a manor that does not violate the law.
        """
        filepath = Path(filename)
        content_hash = md5()
        with open(filepath, "rb") as ebook_file:
            for chunk in ebook_file:
                content_hash.update(chunk)
        identifier = content_hash.hexdigest()
        processed_book = home_data_path(f"{identifier}.epub")
        if processed_book.exists():
            return str(processed_book)
        _temp = TemporaryDirectory()
        temp_path = Path(_temp.name)
        ZipFile(filename).extractall(temp_path)
        with ZipFile(processed_book, "w") as book:
            for file in recursively_iterdir(temp_path):
                if "encryption.xml" in file.name.lower():
                    continue
                book.write(file, file.relative_to(temp_path))
        _temp.cleanup()
        return str(processed_book)
