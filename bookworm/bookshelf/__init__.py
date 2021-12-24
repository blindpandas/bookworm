# coding: utf-8

import sys
import os
import base64
import subprocess
from bookworm import config
from bookworm.document import create_document
from bookworm.concurrency import call_threaded
from bookworm.runtime import CURRENT_PACKAGING_MODE, PackagingMode
from bookworm.document.uri import DocumentUri
from bookworm.service import BookwormService
from bookworm.signals import reader_book_loaded
from bookworm.commandline_handler import BaseSubcommandHandler, register_subcommand
from bookworm.logger import logger
from .local_bookshelf.models import (
    DEFAULT_BOOKSHELF_DATABASE_FILE,
    BaseModel,
    Document,
    Page,
    DocumentFTSIndex,
)
from .interface import BookshelfSettingsPanel, BookshelfMenu, BookshelfWindow
from .tasks import add_document_to_bookshelf


log = logger.getChild(__name__)


DEFAULT_CATEGORY_DB_VALUE = "General"
DEFAULT_CATEGORY_USER_FACING_VALUE = _("General")


@register_subcommand
class DocumentIndexerSubcommandHandler(BaseSubcommandHandler):
    subcommand_name = "document-index"

    @classmethod
    def add_arguments(cls, subparser):
        subparser.add_argument("uri", help="Document URI to open")
        subparser.add_argument(
            "--db-file",
            help="Sqlite database file to store the document to",
            default=os.fspath(DEFAULT_BOOKSHELF_DATABASE_FILE)
        )
        subparser.add_argument(
            "--category",
            help="Category of the given document",
            type=str,
            default=DEFAULT_CATEGORY_DB_VALUE
        )
        subparser.add_argument(
            "--tag",
            help="Tags of the given document",
            action="append",
            dest="tags",
            default=[]
        )

    @classmethod
    def handle_commandline_args(cls, args):
        doc_uri = base64.urlsafe_b64decode(args.uri.encode("utf-8")).decode("utf-8")
        try:
            document = create_document(DocumentUri.from_uri_string(doc_uri))
        except:
            log.exception("Failed to open document for indexing:\n{args.uri}")
            return 1
        else:
            if document.__internal__:
                log.warning(f"{document=} is an internal document. Doing nothing...")
            else:
                add_document_to_bookshelf(document, args.category, args.tags)
        return 0



@register_subcommand
class BookshelfLauncherSubcommand(BaseSubcommandHandler):
    subcommand_name = "bookshelf"

    @classmethod
    def add_arguments(cls, subparser):
        subparser.add_argument(
            "--db-file",
            help="Sqlite database file to store the document to",
            default=os.fspath(DEFAULT_BOOKSHELF_DATABASE_FILE)
        )

    @classmethod
    def handle_commandline_args(cls, args):
        BookshelfWindow.show_standalone(database_file=args.db_file)
        return 0



class BookshelfService(BookwormService):
    name = "bookshelf"
    has_gui = True
    config_spec = {
        "bookshelf": dict(
            auto_add_opened_documents_to_bookshelf="boolean(default=False)",
        ),
    }

    def __post_init__(self):
        BaseModel.create_all()
        reader_book_loaded.connect(self.on_reader_loaded, sender=self.reader, weak=False)

    def get_settings_panels(self):
        return [
            # Translators: the label of a page in the settings dialog
            (100, "bookshelf", BookshelfSettingsPanel, _("Bookshelf")),
        ]

    def process_menubar(self, menubar):
        self.menu = BookshelfMenu(self)
        # Translators: the label of an item in the application menubar
        return (50, self.menu, _("Boo&kshelf"))


    def on_reader_loaded(self, sender):
        if not config.conf["bookshelf"]["auto_add_opened_documents_to_bookshelf"]:
            return
        self.index_document_in_a_subprocess(sender.document.uri)

    @classmethod
    @call_threaded
    def index_document_in_a_subprocess(cls, document_uri):
        log.debug("Book loaded, trying to add it to the shelf...")
        uri = base64.urlsafe_b64encode(document_uri.to_uri_string().encode("utf-8")).decode("utf-8")
        args = [
            DocumentIndexerSubcommandHandler.subcommand_name,
            uri,
            "--category",
            "",
            "--tag",
            ""
        ]
        if CURRENT_PACKAGING_MODE is not PackagingMode.Source:
            executable = sys.executable
        else:
            executable = "pyw.exe"
            args.insert(0, "-m")
            args.insert(1, "bookworm")
        args.insert(0, executable)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(
            args,
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW,
        )
