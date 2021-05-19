# coding: utf-8

import threading
import wx
import trafilatura
from functools import partial
from url_normalize import url_normalize
from platform_utils.clipboard import get_text as get_clipboard_text
from bookworm import app
from bookworm.concurrency import threaded_worker
from bookworm.document_uri import DocumentUri
from bookworm.gui.components import AsyncSnakDialog
from bookworm.utils import gui_thread_safe
from bookworm.base_service import BookwormService
from bookworm.resources import sounds
from bookworm.logger import logger

log = logger.getChild(__name__)


class UrlOpenService(BookwormService):
    name = "url_open"
    config_spec = {}
    has_gui = True

    def __post_init__(self):
        self._cancel_query = threading.Event()

    def process_menubar(self, menubar):
        webservices_menu = (
            wx.GetApp().service_handler.get_service("webservices").web_sservices_menu
        )
        open_url = webservices_menu.Insert(0, -1, _("&Open URL\tCtrl+U"))
        self.open_url_from_clipboard = webservices_menu.Insert(
            1, -1, _("&Open URL From Clipboard\tCtrl+Shift+U")
        )
        self.view.Bind(wx.EVT_MENU, self.onOpenUrl, open_url)
        self.view.Bind(
            wx.EVT_MENU, self.onOpenUrlFromClipboard, self.open_url_from_clipboard
        )

    def get_keyboard_shortcuts(self):
        return {self.open_url_from_clipboard.GetId(): "Ctrl-Shift-U"}

    def onOpenUrl(self, event):
        url = self.view.get_text_from_user(
            # Translators: title of a dialog for entering a URL
            _("Enter URL"),
            # Translators: label of a textbox in a dialog for entering a URL
            _("URL"),
        )
        self.open_url_in_bookworm(url)

    def onOpenUrlFromClipboard(self, event):
        try:
            url = get_clipboard_text()
            return self.open_url_in_bookworm(url)
        except:
            log.exception("Failed to get url from clipboard.", exc_info=True)

    def open_url_in_bookworm(self, url: str):
        if not (url := url.strip()):
            wx.Bell()
            return
        canonical_url = url_normalize(url)
        uri = DocumentUri(format="webpage", path=canonical_url, openner_args={})
        self.view.open_uri(uri)
