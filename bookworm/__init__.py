# coding: utf-8

import gettext

# Make the gettext function _() available in the global namespace, even if no i18n is in use
gettext.install("bookworm", names=["ngettext"])
