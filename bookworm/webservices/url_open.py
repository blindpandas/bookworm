# coding: utf-8

import threading
import wx
import trafilatura
from functools import partial
from url_normalize import url_normalize
from platform_utils.clipboard import get_text as get_clipboard_text
from bookworm.concurrency import threaded_worker
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
        self.open_url_from_clipboard = webservices_menu.Append(-1, _("&Open URL From Clipboard\tCtrl+Shift+V"))
        self.view.Bind(wx.EVT_MENU, self.onOpenUrl, open_url)
        self.view.Bind(wx.EVT_MENU, self.onOpenUrlFromClipboard, self.open_url_from_clipboard)

    def get_keyboard_shortcuts(self):
        return {
            self.open_url_from_clipboard.GetId(): "Ctrl+Shift+V"
        }

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
        AsyncSnakDialog(
            task=partial(trafilatura.fetch_url, canonical_url),
            done_callback=self._on_url_fetched,
            dismiss_callback=lambda: self._cancel_query.set() or True,
            message=_("Getting web page, please wait..."),
            parent=self.view
        )

    def _on_url_fetched(self, future):
        if self._cancel_query.is_set():
            self._cancel_query.clear()
            return
        if not (result := future.result()):
            self.view.notify_user(
                # Translators: title of a messagebox
                _("Error"),
                # Translators: content of a messagebox
                _(
                    "Failed to open web page.\n"
                    "Please make sure that you entered a correct URL, "
                    "and that your computer is connected to the internet"
                ),
                icon=wx.ICON_ERROR
            )
            return
        if self.reader.ready:
            self.view.unloadCurrentEbook()
        html = trafilatura.utils.load_html(result)
        title = trafilatura.metadata.extract_title(html)
        self.view.set_title(title)
        self.view.set_status(title)
        self.view.set_content(trafilatura.process_record(result))
        sounds.navigation.play()
