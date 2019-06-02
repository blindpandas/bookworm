import sys
import wx
from .logger import logger
from .config import setup_config
from .gui.book_viewer import BookViewerWindow


log = logger.getChild(__name__)


def setup_subsystems():
    log.debug("Setting up the configuration subsystem.")
    setup_config
    return True


class BookwormApp(wx.App):

    def OnInit(self):
        mainFrame = BookViewerWindow(None, "Bookworm")
        self.SetTopWindow(mainFrame)
        mainFrame.Show(True)
        return setup_subsystems()
