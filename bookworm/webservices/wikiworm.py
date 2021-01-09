# coding: utf-8

import wx
from bookworm.base_service import BookwormService
from bookworm.logger import logger

log = logger.getChild(__name__)


class WikipediaService(BookwormService):
    name = "wikipedia"
    config_spec = {}
    has_gui = True

    def process_menubar(self, menubar):
        webservices_menu = (
            wx.GetApp().service_handler.get_service("webservices").web_sservices_menu
        )
