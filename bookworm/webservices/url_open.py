# coding: utf-8

import wx
import trafilatura
from url_normalize import url_normalize
from bookworm.concurrency import threaded_worker
from bookworm.utils import gui_thread_safe
from bookworm.base_service import BookwormService
from bookworm.resources import sounds
from bookworm.logger import logger

log = logger.getChild(__name__)


class UrlOpenService(BookwormService):
    name = "url_open"
    config_spec = {}
    has_gui = True

    def process_menubar(self, menubar):
        webservices_menu = (
            wx.GetApp().service_handler.get_service("webservices").web_sservices_menu
        )
        open_url = webservices_menu.Insert(0, -1, _("&Open URL\tCtrl+U"))
        self.view.Bind(wx.EVT_MENU, self.onOpenUrl, open_url)

    def onOpenUrl(self, event):
        url = self.view.get_text_from_user(
            # Translators: title of a dialog for entering a URL
            _("Enter URL"),
            # Translators: label of a textbox in a dialog for entering a URL
            _("URL"),
        )
        canonical_url = url_normalize(url)
        threaded_worker.submit(trafilatura.fetch_url, canonical_url).add_done_callback(
            self.show_page
        )

    @gui_thread_safe
    def show_page(self, future):
        result = future.result()
        if result is None:
            self.view.notify_user("Error", "Failed to get URL")
        else:
            html = trafilatura.utils.load_html(result)
            title = trafilatura.metadata.extract_title(html)
            self.view.set_title(title)
            self.view.set_status(title)
            self.view.set_content(trafilatura.process_record(result))
            sounds.navigation.play()
