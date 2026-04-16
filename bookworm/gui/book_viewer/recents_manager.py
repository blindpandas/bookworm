# coding: utf-8

from bookworm.database import PinnedDocument, RecentDocument
from bookworm.logger import logger

log = logger.getChild(__name__)
_CONTENT_HASH_UNSET = object()


def _get_document_by_uri(model, uri):
    for doc in model.query:
        if uri.is_equal_without_openner_args(doc.uri):
            return doc


def _get_document_by_content_hash(model, content_hash):
    if content_hash is None:
        return
    for doc in model.query:
        if doc.content_hash == content_hash:
            return doc


def get_document_unique(model, document):
    uri = document.uri
    doc = _get_document_by_uri(model, uri)
    content_hash = (
        doc.content_hash
        if doc is not None and doc.content_hash is not None
        else _CONTENT_HASH_UNSET
    )
    if content_hash is _CONTENT_HASH_UNSET:
        content_hash = document.get_content_hash()
    if doc is None:
        doc = _get_document_by_content_hash(model, content_hash)
    if doc is not None:
        doc.title = document.metadata.title
        doc.uri = uri
        if doc.content_hash is None:
            doc.content_hash = content_hash
        model.session.commit()
        return doc
    return model.get_or_create(
        title=document.metadata.title,
        uri=uri,
        content_hash=content_hash,
    )


def add_to_recents(document):
    doc_info = get_document_unique(RecentDocument, document)
    doc_info.record_open()


def remove_from_recents(uri):
    for doc in RecentDocument.query:
        if uri.is_equal_without_openner_args(doc.uri):
            RecentDocument.session.delete(doc)
            RecentDocument.session.commit()


def remove_from_pinned(uri):
    for doc in PinnedDocument.query:
        if uri.is_equal_without_openner_args(doc.uri):
            PinnedDocument.session.delete(doc)
            PinnedDocument.session.commit()


def pin(document):
    get_document_unique(PinnedDocument, document).pin()


def unpin(document):
    get_document_unique(PinnedDocument, document).unpin()


def is_pinned(document):
    return get_document_unique(PinnedDocument, document).is_pinned


def get_recents():
    return RecentDocument.get_recents(limit=10)


def clear_recents():
    RecentDocument.clear_all()


def get_pinned():
    return PinnedDocument.get_pinned(limit=10)


def clear_pinned():
    PinnedDocument.clear_all()
