# coding: utf-8

from bookworm.database import PinnedDocument, RecentDocument
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
    if not document.uri.view_args.get("add_to_recents", True):
        return
    doc_info = get_document_unique(RecentDocument, document)
    doc_info.record_open()


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
