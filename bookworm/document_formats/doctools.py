# coding: utf-8

"""Contains generic utility functions for working with documents."""

import regex as re
from bookworm.utils import search
from bookworm.logger import logger


log = logger.getChild(__name__)


def export_to_plain_text(document_cls, document_path, target_filename, channel):
    """This function runs in a separate process."""
    doc = document_cls(document_path)
    doc.read()
    total = len(doc)
    rv = [doc.metadata.title]
    if rv[0]:
        rv.append(f"\r{'-' * 30}\r")
    for n in range(total):
        text = doc.get_page_content(n)
        rv.append(f"{text}\r\f\r")
        channel.push(n)
    with open(target_filename, "w", encoding="utf8") as file:
        file.write("".join(rv))
    doc.close()
    channel.close()


def search_book(document_cls, document_path, request, channel):
    """This function also runs in a separate process."""
    doc = document_cls(document_path)
    doc.read()
    I = re.I if not request.case_sensitive else 0
    if request.is_regex:
        term = request.term
        term = fr"({term})"
    else:
        term = re.escape(request.term, literal_spaces=True)
        term = fr"({term})"
        if request.whole_word:
            term = fr"\b{term}\b"
    pattern = re.compile(term, I | re.M)
    for n in range(request.from_page, request.to_page + 1):
        found = search(pattern, doc.get_page_content(n))
        if not found:
            channel.push((n, None, None, None))
            continue
        pos, snip = found
        sect = [s for s in doc.toc_tree if n in s.pager]
        sect = doc.toc_tree if not sect else sect[-1]
        channel.push((n, snip, sect.title, pos))
    doc.close()
    channel.close()
