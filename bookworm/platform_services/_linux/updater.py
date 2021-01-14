# coding: utf-8


import wx
from bookworm.logger import logger


log = logger.getChild(__name__)



def perform_update(upstream_version, update_url, sha1hash):
    wx.MessageBox(
        # Translators: the content of a message indicating the availability of an update
        _(
            "A new update for Bookworm is available.\n"
            "\tInstalled Version: {current}\n"
            "\tNew Version: {new}\n"
            "Please check Bookworm's documentation to learn "
            "how to update your version of Bookworm"
        ).format(current=app.version, new=upstream_version),
        # Translators: the title of a message indicating the availability of an update
        _("Update Available"),
        style=wx.ICON_INFORMATION,
    )
