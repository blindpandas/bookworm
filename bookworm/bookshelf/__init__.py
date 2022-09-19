# coding: utf-8


from __future__ import annotations

from bookworm import config
from bookworm.commandline_handler import (BaseSubcommandHandler,
                                          register_subcommand)
from bookworm.concurrency import threaded_worker
from bookworm.logger import logger
from bookworm.service import BookwormService
from bookworm.signals import reader_book_loaded

from .local_bookshelf.tasks import issue_add_document_request
from .viewer_integration import (BookshelfMenu, BookshelfSettingsPanel,
                                 StatefulBookshelfMenuIds)
from .window import run_bookshelf_standalone

log = logger.getChild(__name__)


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
    stateful_menu_ids = StatefulBookshelfMenuIds

    def __post_init__(self):
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
        self.view.fileMenu.Insert(
            6,
            -1,
            # Translators: the label of the bookshelf sub menu found in the file menu of the application
            _("Boo&kshelf"),
            self.menu,
        )

    def on_reader_loaded(self, sender):
        if not config.conf["bookshelf"]["auto_add_opened_documents_to_bookshelf"]:
            return
        log.debug("Book loaded, trying to add it to the shelf...")
        threaded_worker.submit(issue_add_document_request, sender.document.uri)
