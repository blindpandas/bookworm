# coding: utf-8

from bookworm.service import BookwormService
from bookworm.signals import reader_book_loaded
from bookworm.concurrency import process_worker
from .models import BaseModel, Document, Page, DocumentFTSIndex
from .tasks import add_document_to_library


class LibraryService(BookwormService):
    name = "library"
    has_gui = True

    def __post_init__(self):
        BaseModel.create_all()
        reader_book_loaded.connect(
            self.on_reader_loaded,
            sender=self.reader
        )

    def on_reader_loaded(self, sender):
        process_worker.submit(
            add_document_to_library,
            document=sender.document,
            category="Uncategorized",
            tags=["Hello", "world",]
        )
