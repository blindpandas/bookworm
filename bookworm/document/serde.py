# coding: utf-8

"""Serialization/deserialization routines for  documents."""

from bookworm import typehints as t
from bookworm.structured_text import TextRange
from bookworm.document import Section, Pager, TreeStackBuilder


TocTree = t.NewType("TocTree", Section)


def section_to_dict(section: Section) -> dict[str, t.Any]:
    return {
        "title": section.title,
        "pager": section.pager.astuple(),
        "text_range": None
        if (text_range := section.text_range) is None
        else text_range.astuple(),
        "level": section.level,
        "data": section.data,
    }


def section_from_dict(section_data: dict[str, t.Any]) -> Section:
    kwargs = {**section_data, "pager": Pager(*section_data["pager"])}
    if (text_range := kwargs["text_range"]) is not None:
        kwargs["text_range"] = TextRange(*text_range)
    return Section(**kwargs)


def dump_toc_tree(toc_tree: TocTree) -> list[dict[str, t.Any]]:
    return [
        section_to_dict(toc_tree),
        *(section_to_dict(c) for c in toc_tree.iter_children()),
    ]


def load_toc_tree(toc_tree_data: list[dict[str, t.Any]]) -> TocTree:
    data = iter(toc_tree_data)
    root = section_from_dict(next(data))
    stack = TreeStackBuilder(root)
    for sect_data in data:
        stack.push(section_from_dict(sect_data))
    return root
