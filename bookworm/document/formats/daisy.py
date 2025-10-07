"""Daisy 3.0  document format """
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import urllib.parse as urllib_parse
import zipfile
from zipfile import ZipFile

from lxml import etree

from bookworm.document.base import LinkTarget, SinglePageDocument, SINGLE_PAGE_DOCUMENT_PAGER
from bookworm.document import BookMetadata, DocumentCapability as DC, Section
from bookworm.logger import logger
from bookworm.structured_text import TextRange
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
from bookworm.utils import is_external_url

log = logger.getChild(__name__)

@dataclass
class DaisyMetadata:
    """metadata of a daisy book"""
    title: str
    author: str
    publisher: str
    language: str
    path: Path | zipfile.Path

@dataclass
class DaisyNavPoint:
    """Representation of a navigation point"""
    id: str
    content: str
    label: str
    children: list['DaisyNavPoint']

def _parse_opf(path: Path | zipfile.Path) -> DaisyMetadata:
    """Parses the OPF file of a daisy3 book in order to obtain its book metadata"""
    # we have to use path.iterdir() instead of path.glob() because we want to be generic over the type of path this is
    # ZipFile.Path() does not support glob
    entries = [x for x in list(path.iterdir()) if x.name.endswith('.opf')]
    if not entries:
        raise FileNotFoundError("Could not find daisy OPF file")
    opf = entries[0]
    tree = etree.fromstring(opf.read_bytes())
    dc_metadata = tree.find('metadata/dc-metadata', tree.nsmap)
    nsmap = dc_metadata.nsmap
    # We can now obtain the book's information
    metadata = DaisyMetadata(
        title=dc_metadata.find('dc:Title', nsmap).text,
        language=dc_metadata.find('dc:Language', nsmap).text,
        author=dc_metadata.find('dc:Creator', nsmap).text,
        publisher=dc_metadata.find('dc:Publisher', nsmap).text,
        path=path
    )
    return metadata

@dataclass
class DaisyBook:
    """A daisy3 book representation"""
    metadata: DaisyMetadata
    toc: List[DaisyNavPoint]
    nav_ref: Dict[str, str]

def _parse_ncx(path: Path | zipfile.Path) -> List[DaisyNavPoint]:
    """
    Parses a daisy NCX file in order to extract the book's table of content
    """
    entries = [x for x in list(path.iterdir()) if x.name.endswith('.ncx')]
    if not entries:
        # We return an empty list if no NCX file is found
        return []
    tree = etree.fromstring(entries[0].read_bytes())
    # navPoints are all nested inside the navMap
    # We are not interested in the navInfo element, which means that findall() will likely suffice
    nav_points = tree.findall('navMap/navPoint', tree.nsmap)
    def parse_point(element) -> DaisyNavPoint:
        # Only get direct child navPoint elements, not nested ones
        # children_nav_points = [child for child in element if child.tag.endswith('navPoint')]
        children_nav_points = element.findall('navPoint', element.nsmap)
        children = [parse_point(x) for x in children_nav_points]

        _id = element.attrib.get('id')
        label = element.find('navLabel/text', element.nsmap).text
        content = element.find('content', element.nsmap).attrib.get('src')
        return DaisyNavPoint(
            id=_id,
            label=label,
            content=content,
            children=children,
        )
    
    return [parse_point(x) for x in nav_points]


def read_daisy(path: Path) -> DaisyBook:
    """
    Reads a daisy book either from an extracted directory, or from a zipfile
    """
    # TODO: Is it ok to just read from the zipfile rather than extracting it and be done with it?
    if path.is_file() and zipfile.is_zipfile(path):
            zip = ZipFile(path)
            path = zipfile.Path(zip)
    metadata = _parse_opf(path)
    toc = _parse_ncx(path)
    tree_cache = {}
    nav_ref = {}
    def get_smil(file: str):
        entry = tree_cache.get(file)
        if not entry:
            entry = etree.fromstring((path / file).read_bytes())
            tree_cache[file] = entry
        return entry
    def build_nav_ref(point: DaisyNavPoint) -> None:
        for child in point.children:
            build_nav_ref(child)
        file, ref = point.content.split("#")
        tree = get_smil(file)
        child = tree.xpath(f"//*[@id='{ref}']")[0]
        text = child.find('text', child.nsmap).attrib.get('src')
        nav_ref[point.content] = text
    for point in toc:
        build_nav_ref(point)
    
    return DaisyBook(
        metadata=metadata,
        toc=toc,
        nav_ref=nav_ref
    )

class DaisyDocument(SinglePageDocument):
    """Daisy document"""
    format = "daisy"
    name = _("Daisy")
    extensions = ("*.zip",)
    capabilities = (
        DC.TOC_TREE
        | DC.METADATA
        | DC.STRUCTURED_NAVIGATION
        | DC.SINGLE_PAGE
        | DC.LINKS
        | DC.INTERNAL_ANCHORS
    )

    def read(self) -> None:
        super().read()
        self._book: DaisyBook = read_daisy(self.get_file_system_path())
        self.structure = StructuredHtmlParser.from_string(self._get_xml())
        self._toc = self._build_toc()

    def get_content(self) -> str:
        return self.structure.get_text()

    def get_document_semantic_structure(self):
        return self.structure.semantic_elements

    
    def resolve_link(self, link_range) -> LinkTarget:
        href = urllib_parse.unquote(self.structure.link_targets[link_range])
        if is_external_url(href):
            return LinkTarget(url=href, is_external=True)
        else:
            for html_id, text_range in self.structure.html_id_ranges.items():
                if html_id.endswith(href):
                    return LinkTarget(
                        url=href, is_external=False, page=None, position=text_range
                    )

    @property
    def toc_tree(self) -> Section:
        return self._toc

    @property
    def metadata(self) -> BookMetadata:
        return BookMetadata(
            title=self._book.metadata.title,
            author=self._book.metadata.author,
            publisher=self._book.metadata.publisher,
        )

    def _get_xml(self) -> str:        
        fragments: set[str] = {self._book.nav_ref[x.content].split('#')[0] for x in self._book.toc}
        content: list[str] = []
        for text_file in fragments:
            try:
                text_path = self._book.metadata.path / text_file
                if text_path.exists():
                    log.debug(f"Reading from {text_file}")
                    html_content = text_path.read_text(encoding='utf-8')
                    content.append(html_content)
            except (KeyError, FileNotFoundError):
                continue
        return '\n'.join(content)

    def _build_toc(self) -> Section:
        level = 1
        root = Section(
            title=self._book.metadata.title,
            pager = SINGLE_PAGE_DOCUMENT_PAGER,
            level=level,
            text_range=TextRange(0, len(self.structure.get_text())),
        )
        def add_children(stack: Section, entry: DaisyNavPoint, level: int) -> Section:
            item_ref = self._book.nav_ref[entry.content].split('#')[1]
            item_range = self.structure.html_id_ranges.get(item_ref)
            if item_range:
                s = Section(
                    title=entry.label,
                    pager = SINGLE_PAGE_DOCUMENT_PAGER,
                    level = level,
                    text_range=TextRange(*item_range),
                )
                s.children=[add_children(s, x, level+1) for x in entry.children]
                stack.append(s)
            return s
        for entry in self._book.toc:
            add_children(root, entry, level+1 )
        return root
        