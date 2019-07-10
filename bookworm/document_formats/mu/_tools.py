# coding: utf-8

"""Contains utility functions for the mu document reader."""

from hashlib import md5
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from pathlib import Path
from bookworm.document_formats import mu
from bookworm.utils import search, recursively_iterdir
from bookworm.paths import home_data_path
from bookworm.logger import logger


log = logger.getChild(__name__)


def do_export_to_text(document_path, target_filename, queue):
    """This function runs in a separate process."""
    doc = mu.FitzDocument(document_path)
    doc.read()
    total = len(doc)
    rv = [doc.metadata.title]
    if rv[0]:
        rv.append(f"\r{'-' * 30}\r")
    for n in range(total):
        text = doc[n].getText()
        rv.append(f"{text}\r\f\r")
        queue.put(n)
    with open(target_filename, "w", encoding="utf8") as file:
        file.write("".join(rv))
    doc.close()
    queue.put(-1)


def do_search_book(document_path, request, queue):
    """This function also runs in a separate process."""
    doc = mu.FitzDocument(document_path)
    doc.read()
    for n in range(request.from_page, request.to_page + 1):
        found = search(request, doc[n].getText())
        if not found:
            queue.put((n, None, None, None))
            continue
        pos, snip = found
        sect = [s for s in doc.toc_tree if n in s.pager]
        sect = doc.toc_tree if not sect else sect[-1]
        queue.put((n, snip, sect.title, pos))
    doc.close()
    queue.put(-1)


def make_unrestricted_file(filename):
    """Try to remove digital restrictions from the file if found."""
    hashed_filename = md5(filename.lower().encode("utf8")).hexdigest()
    processed_book = home_data_path(hashed_filename)
    if processed_book.exists():
        return str(processed_book)
    _temp = TemporaryDirectory()
    temp_path = Path(_temp.name)
    ZipFile(filename).extractall(temp_path)
    (temp_path / "META-INF\\encryption.xml").unlink()
    with ZipFile(processed_book, "w") as book:
        for file in recursively_iterdir(temp_path):
            book.write(file, file.relative_to(temp_path))
    _temp.cleanup()
    return str(processed_book)
