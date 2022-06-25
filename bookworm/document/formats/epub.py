# coding: utf-8

from __future__ import annotations

import collections.abc
import itertools
import os
import string
from contextlib import suppress
from functools import cached_property, lru_cache
from io import StringIO
from pathlib import Path, PurePosixPath
from urllib import parse as urllib_parse

import dateparser
import ebooklib
import ebooklib.epub
import fitz
import more_itertools
from diskcache import Cache
from lxml import html as lxml_html
from selectolax.parser import HTMLParser

from bookworm.i18n import LocaleInfo
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from bookworm.paths import home_data_path
from bookworm.structured_text import TextRange
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
from bookworm.utils import format_datetime, is_external_url

from .. import SINGLE_PAGE_DOCUMENT_PAGER, BookMetadata, ChangeDocument
from .. import DocumentCapability as DC
from .. import DocumentError, LinkTarget, Section, SinglePageDocument, TreeStackBuilder

log = logger.getChild(__name__)
HTML_FILE_EXTS = {
    ".html",
    ".xhtml",
}


class EpubDocument(SinglePageDocument):

    format = "epub"
    # Translators: the name of a document file format
    name = _("Electronic Publication (EPUB)")
    extensions = ("*.epub",)
    capabilities = (
        DC.TOC_TREE
        | DC.METADATA
        | DC.SINGLE_PAGE
        | DC.STRUCTURED_NAVIGATION
        | DC.TEXT_STYLE
        | DC.ASYNC_READ
        | DC.LINKS
        | DC.INTERNAL_ANCHORS
    )

    def read(self):
        super().read()
        self.epub = ebooklib.epub.read_epub(self.get_file_system_path())
        self.html_content = self.html_content
        self.structure = StructuredHtmlParser.from_string(self.html_content)
        self.toc = self.parse_epub()

    @property
    def toc_tree(self):
        return self.toc

    @cached_property
    def epub_metadata(self):
        info = {}
        for md in tuple(self.epub.metadata.values()):
            info.update(md)
        return {k: v[0][0] for k, v in info.items()}

    @cached_property
    def metadata(self):
        info = self.epub_metadata
        author = info.get("creator", "") or info.get("author", "")
        try:
            desc = HTMLParser(info.get("description", "")).text()
        except:
            desc = None
        if pubdate := dateparser.parse(
            info.get("date", ""),
            languages=[
                self.language.two_letter_language_code,
            ],
        ):
            publish_date = self.language.format_datetime(
                pubdate, date_only=True, format="long", localized=True
            )
        else:
            publish_date = ""
        return BookMetadata(
            title=self.epub.title,
            author=author.removeprefix("By ").strip(),
            description=desc,
            publication_year=publish_date,
            publisher=info.get("publisher", ""),
        )

    @cached_property
    def language(self):
        if (epub_lang := self.epub_metadata.get("language")) is not None:
            try:
                return LocaleInfo(epub_lang)
            except:
                log.exception(
                    "Failed to parse epub language `{epub_lang}`", exc_info=True
                )
        return self.get_language(self.html_content, is_html=True) or LocaleInfo("en")

    def get_content(self):
        return self.structure.get_text()

    def get_document_semantic_structure(self):
        return self.structure.semantic_elements

    def get_document_style_info(self):
        return self.structure.styled_elements

    def resolve_link(self, link_range) -> LinkTarget:
        href = urllib_parse.unquote(self.structure.link_targets[link_range])
        if is_external_url(href):
            return LinkTarget(url=href, is_external=True)
        else:
            for (html_id, text_range) in self.structure.html_id_ranges.items():
                if html_id.endswith(href):
                    return LinkTarget(
                        url=href, is_external=False, page=None, position=text_range
                    )

    def get_cover_image(self):
        if not (
            cover := more_itertools.first(
                self.epub.get_items_of_type(ebooklib.ITEM_COVER), None
            )
        ):
            cover = more_itertools.first(
                filter(
                    lambda item: "cover" in item.file_name.lower(),
                    self.epub.get_items_of_type(ebooklib.ITEM_IMAGE),
                ),
                None,
            )
        if cover:
            return ImageIO.from_bytes(cover.content)
        try:
            with fitz.open(self.get_file_system_path()) as fitz_document:
                return ImageIO.from_fitz_pixmap(fitz_document.get_page_pixmap(0))
        except:
            log.warning(
                "Failed to obtain the cover image for epub document.", exc_info=True
            )

    @lru_cache(maxsize=10)
    def get_section_at_position(self, pos):
        for ((start, end), section) in self.start_positions_for_sections:
            if start <= pos < end:
                return section
        return self.toc_tree

    @cached_property
    def epub_html_items(self) -> tuple[str]:
        if html_items := tuple(self.epub.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
            return html_items
        else:
            return tuple(
                filter(
                    lambda item: os.path.splitext(item.file_name)[1] in HTML_FILE_EXTS,
                    self.epub.items,
                )
            )

    def get_epub_html_item_by_href(self, href):
        if epub_item := self.epub.get_item_with_href("href"):
            return epub_item
        item_name = PurePosixPath(href).name
        return more_itertools.first(
            (
                item
                for item in self.epub_html_items
                if PurePosixPath(item.file_name).name == item_name
            ),
            None,
        )

    def parse_epub(self):
        root = Section(
            title=self.metadata.title,
            pager=SINGLE_PAGE_DOCUMENT_PAGER,
            level=1,
            text_range=TextRange(0, len(self.get_content())),
        )
        id_ranges = {
            urllib_parse.unquote(key): value
            for (key, value) in self.structure.html_id_ranges.items()
        }
        stack = TreeStackBuilder(root)
        toc_entries = self.epub.toc
        if not isinstance(toc_entries, collections.abc.Iterable):
            toc_entries = [
                toc_entries,
            ]
        for sect in self.add_toc_entry(toc_entries, root):
            href = urllib_parse.unquote(sect.data["href"])
            try:
                sect.text_range = TextRange(*id_ranges[href])
            except KeyError:
                # Let's start the dance!
                text_range = None
                # Strip  punctuation as ebooklib, for some reason, strips those from html_ids
                for (h_id, t_range) in id_ranges.items():
                    if (href == h_id.strip("/")) or (
                        href == h_id.strip(string.punctuation)
                    ):
                        text_range = t_range
                        break
                if text_range is None and "#" in href:
                    filename = href.split("#")[0]
                    text_range = id_ranges.get(filename)
                if text_range is None:
                    log.warning(
                        f"Could not determine the starting position for href: {href} and section: {sect!r}"
                    )
                    text_range = (
                        stack.top.text_range.astuple()
                        if stack.top is not root
                        else (0, 0)
                    )
                sect.text_range = TextRange(*text_range)
            stack.push(sect)
        return root

    @cached_property
    def start_positions_for_sections(self):
        sect_starting_poses = [
            (0, self.toc_tree),
        ] + [(sect.text_range.start, sect) for sect in self.toc_tree.iter_children()]
        data = list(
            more_itertools.zip_offset(
                sect_starting_poses, sect_starting_poses, offsets=(0, 1), longest=True
            )
        )
        data[-1] = list(data[-1])
        data[-1][1] = data[-1][0]
        return [((i[0], j[0]), i[1]) for i, j in data]

    def add_toc_entry(self, entries, parent):
        for entry in entries:
            current_level = parent.level + 1
            if type(entry) is ebooklib.epub.Link:
                sect = Section(
                    title=entry.title or self._get_title_for_section(entry.href),
                    pager=SINGLE_PAGE_DOCUMENT_PAGER,
                    level=current_level,
                    parent=parent,
                    data=dict(href=entry.href.lstrip("./")),
                )
                yield sect
            else:
                epub_sect, children = entry
                num_pages = len(children)
                sect = Section(
                    title=epub_sect.title
                    or self._get_title_for_section(epub_sect.href),
                    level=current_level,
                    pager=SINGLE_PAGE_DOCUMENT_PAGER,
                    parent=parent,
                    data=dict(href=epub_sect.href.lstrip("./")),
                )
                yield sect
                yield from self.add_toc_entry(
                    children,
                    parent=sect,
                )

    @cached_property
    def html_content(self):
        cache = Cache(
            self._get_cache_directory(), eviction_policy="least-frequently-used"
        )
        cache_key = self.uri.to_uri_string()
        if cached_html_content := cache.get(cache_key):
            return cached_html_content.decode("utf-8")
        html_content_gen = (
            (item.file_name, item.content) for item in self.epub_html_items
        )
        buf = StringIO()
        for (filename, html_content) in html_content_gen:
            buf.write(self.prefix_html_ids(filename, html_content))
            buf.write("\n<br/>\n")
        html_content = self.build_html(
            title=self.epub.title, body_content=buf.getvalue()
        )
        cache.set(cache_key, html_content.encode("utf-8"))
        return html_content

    def prefix_html_ids(self, filename, html):
        tree = lxml_html.fromstring(html)
        tree.make_links_absolute(
            filename, resolve_base_href=False, handle_failures="ignore"
        )
        if os.path.splitext(filename)[1] in HTML_FILE_EXTS:
            for node in tree.xpath("//*[@id]"):
                node.set("id", filename + "#" + node.get("id"))
        try:
            tree.remove(tree.head)
            tree.body.tag = "section"
        except:
            pass
        tree.tag = "div"
        tree.insert(0, tree.makeelement("header", attrib={"id": filename}))
        return lxml_html.tostring(tree, method="html", encoding="unicode")

    def build_html(self, title, body_content):
        return (
            "<!doctype html>\n"
            '<html class="no-js" lang="">\n'
            "<head>\n"
            '<meta charset="utf-8">'
            f"<title>{title}</title>\n"
            "</head>\n"
            "<body>\n"
            f"{body_content}\n"
            "</body>\n"
            "</html>"
        )

    def _get_title_for_section(self, href):
        filename = href.split("#")[0] if "#" in href else href
        html_doc = self.get_epub_html_item_by_href(filename)
        if html_doc is not None:
            if title_list := lxml_html.fromstring(html_doc.content).xpath(
                "/html/head/title//text()"
            ):
                return title_list[0]
        else:
            log.warning(f"Could not resolve href: {href}")
        return ""

    def _get_cache_directory(self):
        return os.fspath(home_data_path(".parsed_epub_cache"))
