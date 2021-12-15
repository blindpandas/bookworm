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


def add_document_to_bookshelf(
    document: BaseDocument,
    category_name,
    tags_names: list[str]
):
    """Add the given document to the bookshelf database."""
    if (existing_doc := Document.get_or_none(uri=document.uri)) is not None:
        log.debug("Document already in the database. Checking index...")
        db_page_count = (
            DocumentFTSIndex.select()
            .where(DocumentFTSIndex.document_id == existing_doc.get_id())
            .count()
        )
        if db_page_count == len(document):
            log.debug("Document index is OK")
            return
        else:
            log.debug("Document index is not well formed. Rebuilding index...")
            existing_doc.delete_instance()
    cover_image = document.get_cover_image()
    metadata = document.metadata
    author, __ = Author.get_or_create(name=metadata.author)
    format, __ = Format.get_or_create(name=document.uri.format)
    category, __ = Category.get_or_create(name=category_name)
    tags = [Tag.get_or_create(name=t)[0] for t in tags_names]
    log.debug("Adding document to the database ")
    doc = Document.create(
        uri=document.uri,
        title=metadata.title,
        authors=[
            author,
        ],
        publication_date=metadata.publication_year,
        cover_image=cover_image,
        format=format,
        category=category,
        tags=tags,
    )
    doc.save()
    doc_id = doc.get_id()
    fields = [Page.number, Page.content, Page.document]
    page_objs = ((page.index, page.get_text(), doc) for page in document)
    for batch in more_itertools.chunked(page_objs, 100):
        Page.insert_many(batch, fields).execute()
    DocumentFTSIndex.add_document_to_search_index(doc.get_id()).execute()
    DocumentFTSIndex.optimize()
