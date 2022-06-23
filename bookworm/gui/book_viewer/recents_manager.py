# coding: utf-8

from bookworm.database import RecentDocument, PinnedDocument
from bookworm.logger import logger


log = logger.getChild(__name__)


def get_document_unique(model, document):
    uri = document.uri
    for doc in model.query:
        if uri.is_equal_without_openner_args(doc.uri):
            doc.uri = uri
            model.session.commit()
            return doc
    return model.get_or_create(title=document.metadata.title, uri=uri)


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
