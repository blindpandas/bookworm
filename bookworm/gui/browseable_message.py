# -*- coding: utf-8 -*-
# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2008-2020 NV Access Limited, James Teh, Dinesh Kaushal, Davy Kager, André-Abush Clause,
# Babbage B.V., Leonard de Ruijter, Michael Curran, Accessolutions, Julien Cochuyt
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

import os
import wx
from ctypes import windll, byref, POINTER, addressof, c_size_t
from comtypes import IUnknown
from comtypes import automation
from html import escape
from bookworm.paths import resources_path



# From urlmon.h
URL_MK_UNIFORM = 1

# Dialog box properties
DIALOG_OPTIONS = "resizable:yes;help:no"

# dwDialogFlags for ShowHTMLDialogEx from mshtmhst.h
HTMLDLG_NOUI = 0x0010
HTMLDLG_MODAL = 0x0020
HTMLDLG_MODELESS = 0x0040
HTMLDLG_PRINT_TEMPLATE = 0x0080
HTMLDLG_VERIFY = 0x0100


def browseable_message(message, title=None, is_html=False):
    """Present a message to the user that can be read in browse mode.
    The message will be presented in an HTML document.
    @param message: The message in either html or text.
    @type message: str
    @param title: The title for the message.
    @type title: str
    @param is_html: Whether the message is html
    @type is_html: boolean
    """
    htmlFileName = os.fspath(resources_path("message.html"))
    moniker = POINTER(IUnknown)()
    windll.urlmon.CreateURLMonikerEx(0, htmlFileName, byref(moniker), URL_MK_UNIFORM)
    if not title:
        # Translators: The title for the dialog used to present general messages in browse mode.
        title = _("Message")
    if not is_html:
        message = f"<pre>{escape(message)}</pre>"
    dialogString = f"{title};{message}"
    dialogArguements = automation.VARIANT(dialogString)
    windll.mshtml.ShowHTMLDialogEx(
        wx.GetApp().mainFrame.GetHandle(),
        moniker,
        HTMLDLG_MODELESS,
        c_size_t(addressof(dialogArguements)),
        DIALOG_OPTIONS,
        None,
    )
