# coding: utf-8

import sys
import os
import urllib.parse
import requests
from bookworm import config
from bookworm import local_server
from bookworm.document import create_document
from bookworm.document.uri import DocumentUri
from bookworm.concurrency import process_worker, call_threaded
from bookworm.service import BookwormService
from bookworm.signals import reader_book_loaded, local_server_booting
from bookworm.commandline_handler import (
    BaseSubcommandHandler,
    register_subcommand,
    run_subcommand_in_a_new_process,
)
from bookworm.logger import logger
from .local_bookshelf.models import (
    DEFAULT_BOOKSHELF_DATABASE_FILE,
    BaseModel,
    Document,
    Page,
    DocumentFTSIndex,
)
from .local_bookshelf.tasks import add_document_to_bookshelf
from .viewer_integration import BookshelfSettingsPanel, BookshelfMenu
from .window import run_bookshelf_standalone


log = logger.getChild(__name__)


ADD_TO_BOOKSHELF_URL_PREFIX = '/add-to-bookshelf'


@local_server_booting.connect
def _add_document_index_endpoint(sender):
    from bottle import request, abort

    @sender.route(ADD_TO_BOOKSHELF_URL_PREFIX, method='POST')
    def add_to_bookshelf_view():
        data = request.json
        doc_uri = data['document_uri']
        try:
            document = create_document(DocumentUri.from_uri_string(doc_uri))
        except:
            log.exception(f"Failed to open document: {doc_uri}", exc_info=True)
            abort(400, f'Failed to open document: {doc_uri}')
        else:
            if document.__internal__:
                abort(400, f'Document is an internal document: {doc_uri}')
            else:
                process_worker.submit(
                    add_document_to_bookshelf,
                    document,
                    data['category'],
                    data['tags'],
                    data['database_file']
                )
                return {'status': 'OK', 'document_uri': doc_uri}


@register_subcommand
class BookshelfSubcommandHandler(BaseSubcommandHandler):
    subcommand_name = "bookshelf"

    @classmethod
    def add_arguments(cls, subparser):
        pass

    @classmethod
    def handle_commandline_args(cls, args):
        run_bookshelf_standalone()
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
        reader_book_loaded.connect(
            self.on_reader_loaded, sender=self.reader, weak=False
        )

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
        url = urllib.parse.urljoin(
            local_server.get_local_server_netloc(),
            ADD_TO_BOOKSHELF_URL_PREFIX
        )
        data = {
            'document_uri': document_uri.to_uri_string(),
            'category': 'General',
            'tags': [],
            'database_file': '',
        }
        res = requests.post(url, json=data) 
        log.debug(f"Indexed document: {res}")
