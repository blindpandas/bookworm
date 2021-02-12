# coding: utf-8

import sys
import os
import platform
import argparse
import multiprocessing
import wx
from bookworm import app as appinfo
from bookworm.paths import logs_path
from bookworm.config import setup_config
from bookworm.i18n import setup_i18n, set_wx_locale
from bookworm.database import init_database
from bookworm.platform_services.shell import shell_integrate, shell_disintegrate
from bookworm.signals import app_started, app_shuttingdown
from bookworm.runtime import PackagingMode, IS_RUNNING_PORTABLE, CURRENT_PACKAGING_MODE
from bookworm.service_handler import ServiceHandler
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.gui.settings import show_file_association_dialog
from bookworm.logger import logger


log = logger.getChild(__name__)


class BookwormApp(wx.App):
    """The application class."""

    def OnInit(self):
        self.Bind(wx.EVT_END_SESSION, self.onEndSession)
        return True

    def OnAssert(self, file, line, cond, msg):
        message = f"{file}, line {line}:\nassert {cond}: {msg}"
        log.warning(message, codepath="wx", stack_info=True)

    def onEndSession(self, event):
        self.OnExit()
        app_shuttingdown.send(self)

    def OnExit(self):
        return 0


# The following tasks are autonomous. They are executed
#  by invoking the executable with a command line flag
TASKS = {
    "shell_integrate": lambda v: shell_integrate(),
    "shell_disintegrate": lambda v: shell_disintegrate(),
    "setup_file_assoc": show_file_association_dialog,
}


def setupSubsystems():
    log.debug("Setting up application subsystems.")
    log.debug("Setting up the configuration subsystem.")
    setup_config()
    log.debug("Setting up the internationalization subsystem.")
    setup_i18n()
    log.debug("Initializing the database subsystem.")
    init_database()


def init_app_and_run_main_loop():
    log.info("Starting Bookworm.")
    log.info(f"Bookworm Version: {appinfo.version}")
    log.info(f"Python version: {sys.version}")
    log.info(f"Platform: {platform.platform()}")
    log.info(f"Windows version: {wx.GetOsDescription()}")
    log.info(f"Application architecture: {appinfo.arch}")
    if CURRENT_PACKAGING_MODE is PackagingMode.Portable:
        log.info("Running a portable copy of Bookworm.")
    elif CURRENT_PACKAGING_MODE is PackagingMode.Installed:
        log.info("Running an installed copy of Bookworm.")
    elif CURRENT_PACKAGING_MODE is PackagingMode.Source:
        log.info("Running Bookworm from source.")

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default=None)
    parser.add_argument("--debug", action="store_true")
    if not IS_RUNNING_PORTABLE:
        parser.add_argument("--shell-integrate", action="store_true")
        parser.add_argument("--shell-disintegrate", action="store_true")
        parser.add_argument("--setup-file-assoc", action="store_true")
    appinfo.args, appinfo.extra_args = parser.parse_known_args()
    if appinfo.args.debug or os.environ.get("BOOKWORM_DEBUG"):
        appinfo.debug = True

    log.info(f"Debug mode is {'on' if appinfo.debug else 'off'}.")
    if appinfo.is_frozen:
        multiprocessing.freeze_support()
    setupSubsystems()

    wxlogfilename = logs_path("wx.log") if not appinfo.debug else None
    app = BookwormApp(redirect=True, useBestVisual=True, filename=wxlogfilename)
    set_wx_locale(appinfo.current_language)
    mainFrame = app.mainFrame = BookViewerWindow(None, appinfo.display_name)
    app.service_handler = ServiceHandler(mainFrame)
    app.service_handler.register_builtin_services()
    mainFrame.finalize_gui_creation()
    app_started.send(app)
    log.info("The application has started successfully.")

    # Process known cmd arguments
    for flag, func in TASKS.items():
        flag_value = getattr(appinfo.args, flag, None)
        if flag_value:
            log.info("The application is running in command line mode.")
            log.info(f"Invoking command `{flag}` with value `{flag_value}`.")
            appinfo.command_line_mode = True
            return func(flag_value)

    log.info("Preparing to show the application GUI.")
    app.SetTopWindow(mainFrame)
    mainFrame.Show(True)
    arg_file = os.path.abspath(appinfo.args.filename or "")
    if os.path.isfile(arg_file):
        log.info("The application was invoked with a file")
        mainFrame.open_file(arg_file)

    app.MainLoop()
    log.info("Shutting down the application.")
    app_shuttingdown.send(app)


def run():
    try:
        init_app_and_run_main_loop()
        log.info("The application has exited gracefully.")
    except BaseException as e:
        log.critical(f"An unhandled error has occured.", exc_info=True)
        raise
