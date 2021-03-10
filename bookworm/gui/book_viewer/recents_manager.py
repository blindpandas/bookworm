# coding: utf-8

from bookworm.database import RecentDocument
from bookworm.logger import logger


log = logger.getChild(__name__)



def add_to_recents(document):
    current_uri = document.uri
    doc_info = None
    for doc in RecentDocument.query:
        if current_uri.is_equal_without_openner_args(doc.uri):
            doc.uri = current_uri
            RecentDocument.session.commit()
            doc_info = doc
            break
    if doc_info is None:
        doc_info = RecentDocument.get_or_create(
            title=document.metadata.title,
            uri=current_uri
        )
    doc_info.record_open()

def get_recents():
    return RecentDocument.get_recents(limit=10)

def clear_recents(self):
    RecentDocument.clear_all()
