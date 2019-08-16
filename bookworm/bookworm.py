# coding: utf-8

import argparse
import wx
from bookworm import app as appinfo
from bookworm.paths import logs_path
from bookworm.config import setup_config
from bookworm.i18n import setup_i18n
from bookworm.database import init_database
from bookworm.signals import app_started, app_shuttingdown
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.logger import logger


log = logger.getChild(__name__)


class BookwormApp(wx.App):
    def setupSubsystems(self):
        log.debug("Setting up application subsystems.")
        log.debug("Setting up the configuration subsystem.")
        setup_config()
        log.debug("Setting up the internationalization subsystem.")
        setup_i18n()
        log.debug("Initializing the database subsystem.")
        init_database()

    def OnInit(self):
        log.debug("Starting the application.")
        self.setupSubsystems()
        self.mainFrame = BookViewerWindow(None, appinfo.display_name)
        self.SetTopWindow(self.mainFrame)
        self.mainFrame.Show(True)
        self.Bind(wx.EVT_END_SESSION, self.onEndSession)
        app_started.send(self)
        log.debug("The application has started successfully.")
        return True

    def OnAssert(self, file, line, cond, msg):
        message = f"{file}, line {line}:\nassert {cond}: {msg}"
        log.warning(message, codepath="wx", stack_info=True)

    def onEndSession(self, event):
        app_shuttingdown.send(self)

    def OnExit(self):
        log.debug("Shutting down the application.")
        return 0


def init_app_and_run_main_loop():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default=None)
    parser.add_argument("--debug", action="store_true")
    appinfo.args, appinfo.extra_args = parser.parse_known_args()
    if appinfo.args.debug:
        appinfo.debug = True
    log.debug(f"Debug mode is {'on' if appinfo.debug else 'off'}.")
    if appinfo.is_frozen:
        from multiprocessing import freeze_support

        freeze_support()
    wxlogfilename = logs_path("wx.log") if not appinfo.debug else None
    app = BookwormApp(redirect=True, useBestVisual=True, filename=wxlogfilename)
    app.MainLoop()
    app_shuttingdown.send(app)


def main():
    try:
        init_app_and_run_main_loop()
        log.debug("The application has exited grasefully.")
    except BaseException as e:
        log.exception(f"An unhandled error has occured.")
        if appinfo.debug:
            raise e
        wx.Exit()
