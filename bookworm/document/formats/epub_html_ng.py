# coding: utf-8

from __future__ import annotations
import collections.abc
import os.path
import string
import itertools
import more_itertools
import ebooklib
import ebooklib.epub
import fitz
from contextlib import suppress
from io import StringIO
from functools import cached_property, lru_cache
from pathlib import Path, PurePosixPath
from urllib import parse as urllib_parse
from diskcache import Cache
from lxml import html as lxml_html
from selectolax.parser import HTMLParser
from bookworm.i18n import LocaleInfo
from bookworm.structured_text import TextRange
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
from bookworm.utils import is_external_url
from bookworm.paths import home_data_path
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from .. import (
    SinglePageDocument,
    BookMetadata,
    Section,
    LinkTarget,
    DocumentCapability as DC,
    TreeStackBuilder,
    ChangeDocument,
    DocumentError,
    SINGLE_PAGE_DOCUMENT_PAGER,
)


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
        self.html_content = self.get_html_content()
        self.structure = StructuredHtmlParser.from_string(self.html_content)
        self.toc = self.parse_epub()

    @property
    def toc_tree(self):
        return self.toc

    @cached_property
    def metadata(self):
        epub_metadata = tuple(self.epub.metadata.values())
        info = {}
        for md in epub_metadata:
            info.update(md)
        info = {k: v[0][0] for k,v in info.items()}
        author = (
            info.get("creator", "")
            or info.get("author", "")
        )
        try:
            desc = HTMLParser(info.get("description", "")).text()
        except:
            desc = None
        return BookMetadata(
            title=self.epub.title,
            author=author.removeprefix("By ").strip(),
            description=desc,
            publication_year=info.get("date", ""),
            publisher=info.get("publisher", "")
        )

    @cached_property
    def language(self):
        content = (
            file.content for file in self.epub.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        )
        sample_html_pages = b"<br/>".join(more_itertools.take(20, content))
        return self.get_language(sample_html_pages, is_html=True) or LocaleInfo("en")

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
                    title=entry.title,
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
                    title=epub_sect.title,
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

    def get_html_content(self):
        cache = Cache(
            self._get_cache_directory(), eviction_policy="least-frequently-used"
        )
        cache_key = self.uri.to_uri_string()
        if cached_html_content := cache.get(cache_key):
            return cached_html_content.decode("utf-8")
        html_items = tuple(self.epub.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        if not html_items:
            html_items = tuple(
                filter(
                    lambda item: os.path.splitext(item.file_name)[1] in HTML_FILE_EXTS,
                    self.epub.items,
                )
            )
        html_content_gen = ((item.file_name, item.content) for item in html_items)
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
        tree.make_links_absolute(filename)
        if os.path.splitext(filename)[1] in HTML_FILE_EXTS:
            for node in tree.cssselect("[id]"):
                node.set("id", filename + "#" + node.get("id"))
        with suppress(IndexError):
            tree.remove(tree.head)
            tree.body.tag = "section"
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

    def _get_cache_directory(self):
        return str(home_data_path(".parsed_epub_cache"))
