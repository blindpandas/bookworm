"""Daisy 3.0  document format """
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from zipfile import ZipFile

from lxml import etree

@dataclass
class DaisyMetadata:
    """metadata of a daisy book"""
    title: str
    author: str
    publisher: str
    language: str
    path: str

@dataclass
class DaisyNavPoint:
    """Representation of a navigation point"""
    id: str
    content: str
    label: str


def _parse_opf(path: Path) -> DaisyMetadata:
    entries = list(path.glob("*.opf"))
    if not entries:
        raise FileNotFoundError("Could not find daisy OPF file")
    opf = entries[0]
    with open(opf, 'rb') as f:
        tree = etree.fromstring(f.read())
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
    metadata: DaisyMetadata
    toc: List[DaisyNavPoint]
    nav_ref: Dict[str, str]

def _parse_ncx(path: Path) -> List[DaisyNavPoint]:
    entries = list(path.glob("*.ncx"))
    if not entries:
        return []
    with open(entries[0], 'rb') as f:
        tree = etree.fromstring(f.read())
    # navPoints are all nested inside the navMap
    # We are not interested in the navInfo element, which means that findall() will likely suffice
    nav_points = tree.findall('navMap/navPoint', tree.nsmap)
    def parse_point(element) -> DaisyNavPoint:
        _id = element.attrib.get('id')
        label = element.find('navLabel/text', element.nsmap).text
        content = element.find('content', element.nsmap).attrib.get('src')
        return DaisyNavPoint(
            id=_id,
            label=label,
            content=content
        )
    
    return [parse_point(x) for x in nav_points]


def read_daisy(path: Path) -> DaisyBook:
    metadata = _parse_opf(path)
    toc = _parse_ncx(path)
    tree_cache = {}
    nav_ref = {}
    def get_smil(file: str):
        entry = tree_cache.get(file)
        if not entry:
            with open(path / file, 'rb') as f:
                entry = etree.parse(f)
            tree_cache[file] = entry
        return entry
    for point in toc:
        file, ref = point.content.split("#")
        tree = get_smil(file)
        child = tree.xpath(f"//*[@id='{ref}']")[0]
        text = child.find('text', child.nsmap).attrib.get('src')
        nav_ref[point.content] = text
    
    return DaisyBook(
        metadata=metadata,
        toc=toc,
        nav_ref=nav_ref
    )
