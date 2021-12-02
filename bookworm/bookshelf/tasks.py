# coding: utf-8

import more_itertools
import bookworm.typehints as t
from bookworm.document.base import BaseDocument
from bookworm.logger import logger
from .models import (
    Author,
    Category,
    Format,
    Document,
    Page,
    Tag,
    DocumentFTSIndex,
)



log = logger.getChild(__name__)


def add_document_to_bookshelf(document: BaseDocument, category=None, tags: t.Iterable[str]=()):
    """Add the given document to the bookshelf database."""
    if Document.get_or_none(uri=document.uri) is not None:
        return
    try:
        cover_image = document.get_cover_image()
    except NotImplementedError:
        cover_image = None
    metadata = document.metadata
    author, __ = Author.get_or_create(name=metadata.author)
    format, __ = Format.get_or_create(name=document.uri.format)
    category, __ = Category.get_or_create(name=category)
    tags = [
        Tag.get_or_create(name=t)[0]
        for t in tags
    ]
    doc = Document.create(
        uri=document.uri,
        title=metadata.title,
        authors=[author,],
        publication_date=metadata.publication_year,
        cover_image=cover_image,
        format=format,
        category=category,
        tags=tags,
    )
    doc.save()
    doc_id = doc.get_id()
    fields = [Page.number, Page.content, Page.document]
    page_objs = (
        (
            page.index,
            page.get_text(),
            doc
        )
        for page in document
    )
    for batch in more_itertools.chunked(page_objs, 100):
        Page.insert_many(batch, fields).execute()
    DocumentFTSIndex.add_document_to_search_index(doc.get_id()).execute()
    DocumentFTSIndex.optimize()
