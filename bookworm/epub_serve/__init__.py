# coding: utf-8

from __future__ import annotations
import sys
import os
import time
import atexit
import contextlib
import wx
from multiprocessing.shared_memory import SharedMemory
import requests
import waitress
from functools import partial
from bookworm.utils import is_free_port, find_free_port
from bookworm.commandline_handler import BaseSubcommandHandler, register_subcommand, run_subcommand_in_a_new_process
from bookworm.service import BookwormService
from bookworm.signals import reader_book_loaded
from bookworm.gui.components import AsyncSnakDialog
from bookworm.document.formats import EpubDocument
from bookworm.logger import logger
from .webapp import EpubServingApp


log = logger.getChild(__name__)


BOOKWORM_EPUB_SERVE_DEFAULT_PORT = 31585
BOOKWORM_EPUB_SERVE_SHARED_MEMORY_NAME = 'bkw.epub.serve.port'
BOOKWORM_EPUB_SERVE_SHARED_MEMORY_SIZE = 32
SERVER_READY_TIMEOUT = 120


@register_subcommand
class EpubServeSubcommand(BaseSubcommandHandler):
    subcommand_name = "epub_serve"

    @classmethod
    def add_arguments(cls, subparser):
        pass

    @classmethod
    def handle_commandline_args(cls, args):
        if (server_port := cls.get_epub_server_port()) is not None:
            log.info(f"Epub server is already running at port {server_port}")
        else:
            log.info("Server is not running.")
            cls.run_server()
        return 0

    @staticmethod
    def run_server():
        log.debug("Starting epub server...")
        server_port = BOOKWORM_EPUB_SERVE_DEFAULT_PORT if is_free_port(BOOKWORM_EPUB_SERVE_DEFAULT_PORT) else find_free_port()
        log.debug(f"Choosing port {server_port} to run at...")
        shm = SharedMemory(BOOKWORM_EPUB_SERVE_SHARED_MEMORY_NAME, create=True, size=BOOKWORM_EPUB_SERVE_SHARED_MEMORY_SIZE)
        shm.buf[:BOOKWORM_EPUB_SERVE_SHARED_MEMORY_SIZE] = server_port.to_bytes(BOOKWORM_EPUB_SERVE_SHARED_MEMORY_SIZE, sys.byteorder)
        atexit.register(shm.unlink)
        app = EpubServingApp()
        log.debug(f"Server is running at: localhost:{server_port}/")
        waitress.serve(app, listen=f'localhost:{server_port}')
        shm.unlink()

    @staticmethod
    def get_epub_server_port():
        try:
            shm = SharedMemory(BOOKWORM_EPUB_SERVE_SHARED_MEMORY_NAME, create=False)
        except FileNotFoundError:
            return
        else:
            retval = int.from_bytes(bytes(shm.buf), sys.byteorder)
            shm.close()
            return retval


class EpubServeService(BookwormService):
    name = "epub_serve"
    has_gui = True
    stateful_menu_ids = []

    def __post_init__(self):
        reader_book_loaded.connect(self.on_reader_loaded, sender=self.reader, weak=False)

    def process_menubar(self, menubar):
        self.menubar = menubar
        self.openOnWebReaderId  = wx.NewIdRef()
        self.stateful_menu_ids.append(self.openOnWebReaderId)
        self.view.documentMenu.Append(
            self.openOnWebReaderId,
            _("Open on &web Viewer"),
            _("Open the current EPUB book on the browser")
        )
        self.view.Bind(
            wx.EVT_MENU,
            self.onOpenonWeb,
            id=self.openOnWebReaderId
        )

    def on_reader_loaded(self, sender):
        self.menubar.Enable(
            self.openOnWebReaderId,
            isinstance(sender, EpubDocument)
        )

    def onOpenonWeb(self, event):
        task = partial(
            self.retreive_web_viewer_url,
            os.fspath(self.reader.document.get_file_system_path())
        )
        AsyncSnakDialog(
            task=task,
            done_callback=self.server_data_ready_callback,
            message=_("Openning in web viewer..."),
            parent=self.view
        )

    def retreive_web_viewer_url(self, filename):
        server_port = EpubServeSubcommand.get_epub_server_port()
        if server_port is not None:
            return self.make_epub_viewer_url(server_port, filename)
        run_subcommand_in_a_new_process(args=["epub_serve"])
        now = time.monotonic()
        while (now - time.monotonic()) <= SERVER_READY_TIMEOUT:
            server_port = EpubServeSubcommand.get_epub_server_port()
            if server_port is not None:
                return self.make_epub_viewer_url(server_port, filename)
            else:
                time.sleep(1)
        raise TimeoutError("Could not get server IP within 30 seconds")

    def server_data_ready_callback(self, future):
        self.view.go_to_webpage(future.result())

    def make_epub_viewer_url(self, server_port, filename):
        res = requests.post(f'http://localhost:{server_port}/open_epub', json=dict(filename=filename))
        book_uid = res.json()['book_uid']
        return f'http://localhost:{server_port}/?epub=epubs/{book_uid}'
