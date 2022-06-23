# coding: utf-8

from __future__ import annotations
import os
import wx
import requests
from functools import partial
import urllib.parse
from bookworm import local_server
from bookworm.service import BookwormService
from bookworm.signals import reader_book_loaded, local_server_booting
from bookworm.gui.components import AsyncSnakDialog
from bookworm.document.formats import EpubDocument
from bookworm.logger import logger
from .webapp import EpubServingApp, EPUB_SERVE_APP_PREFIX


log = logger.getChild(__name__)


@local_server_booting.connect
def _register_epub_serving_app(sender):
    sender.mount(EPUB_SERVE_APP_PREFIX, EpubServingApp())


class EpubServeService(BookwormService):
    name = "epub_serve"
    has_gui = True
    stateful_menu_ids = []

    def __post_init__(self):
        self.view.add_load_handler(self._on_reader_loaded)

    def process_menubar(self, menubar):
        self.menubar = menubar
        self.openOnWebReaderId = wx.NewIdRef()
        self.stateful_menu_ids.append(self.openOnWebReaderId)
        self.view.documentMenu.Append(
            self.openOnWebReaderId,
            _("Open in &web Viewer"),
            _("Open the current EPUB book in the browser"),
        )
        self.view.Bind(wx.EVT_MENU, self.onOpenonWeb, id=self.openOnWebReaderId)

    def _on_reader_loaded(self, sender):
        self.view.documentMenu.Enable(
            self.openOnWebReaderId, isinstance(sender.document, EpubDocument)
        )

    def onOpenonWeb(self, event):
        task = partial(
            self.retreive_web_viewer_url,
            os.fspath(self.reader.document.get_file_system_path()),
        )
        AsyncSnakDialog(
            task=task,
            done_callback=self.server_data_ready_callback,
            message=_("Openning in web viewer..."),
            parent=self.view,
        )

    def retreive_web_viewer_url(self, filename):
        netloc = local_server.get_local_server_netloc()
        base_url = urllib.parse.urljoin(netloc, EPUB_SERVE_APP_PREFIX)
        log.info(base_url)
        res = requests.post(
            urllib.parse.urljoin(base_url, "open_epub"), json=dict(filename=filename)
        )
        book_uid = res.json()["book_uid"]
        return urllib.parse.urljoin(base_url, f"?epub=epubs/{book_uid}")

    def server_data_ready_callback(self, future):
        try:
            web_viewe_url = future.result()
        except:
            log.exception("Error opening the web viewer", exc_info=True)
            self.view.notify_user(
                _("Failed to launch web viewer"),
                _("An error occurred while opening the web viewer. Please try again."),
                icon=wx.ICON_ERROR,
            )
        else:
            self.view.go_to_webpage(web_viewe_url)
