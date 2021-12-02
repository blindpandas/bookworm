# coding: utf-8

import sys
import subprocess
import win32api
from bookworm.document import create_document
from bookworm.document.uri import DocumentUri
from bookworm.service import BookwormService
from bookworm.signals import reader_book_loaded
from bookworm.concurrency import process_worker
from bookworm.commandline_handler import BaseSubcommandHandler, register_subcommand
from bookworm.logger import logger
from .models import BaseModel, Document, Page, DocumentFTSIndex
from .tasks import add_document_to_bookshelf


log = logger.getChild(__name__)



@register_subcommand
class BookshelfSubcommandHandler(BaseSubcommandHandler):
    subcommand_name = "bookshelf"

    @classmethod
    def add_arguments(cls, subparser):
        subparser.add_argument("uri", help="Document URI to open")
        subparser.add_argument("--category", help="Category of the given document", type=str, default=None)
        subparser.add_argument("--tags", help="Tags of the given document", type=str, default=None)

    @classmethod
    def handle_commandline_args(cls, args):
        try:
            doc = create_document(DocumentUri.from_uri_string(args.uri))
        except:
            log.exception("Failed to open document for indexing")
    else:
        if document.__internal__:
            log.info(f"{document=} is an internal document.")
        else:
            add_document_to_bookshelf(doc, args.category, args.tags)
        return 0


class LibraryService(BookwormService):
    name = "bookshelf"
    has_gui = True

    def __post_init__(self):
        BaseModel.create_all()
        reader_book_loaded.connect(
            self.on_reader_loaded,
            sender=self.reader
        )

    def on_reader_loaded(self, sender):
        args = subprocess.list2cmdline([
            'bookshelf',
            f'"{sender.document.uri}"',
            "--category",
            "General",
            "--tags",
            "no,tags",
        ])
        win32api.ShellExecute(
            0,
            "open",
            sys.executable,
            args,
            "",
            5
        )
