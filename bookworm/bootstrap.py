# coding: utf-8

import multiprocessing
import os
import platform
import sys
from functools import partial

import wx

from bookworm import app as appinfo
from bookworm.commandline_handler import (BaseSubcommandHandler,
                                          handle_app_commandline_args,
                                          register_subcommand)
from bookworm.config import setup_config
from bookworm.database import init_database
from bookworm.document.uri import DocumentUri
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.gui.settings import show_file_association_dialog
from bookworm.i18n import setup_i18n
from bookworm.local_server import LocalServerSubcommand
from bookworm.logger import configure_logger, logger
from bookworm.paths import logs_path
from bookworm.runtime import (CURRENT_PACKAGING_MODE, IS_IN_MAIN_PROCESS,
                              IS_RUNNING_PORTABLE, PackagingMode)
from bookworm.service.handler import ServiceHandler
from bookworm.shell import shell_disintegrate, shell_integrate
from bookworm.signals import (app_shuttingdown, app_started, app_starting,
                              app_window_shown, reader_page_changed)

log = logger.getChild(__name__)


@register_subcommand
class LauncherSubcommandHandler(BaseSubcommandHandler):
    subcommand_name = "launcher"

    @classmethod
    def add_arguments(cls, subparser):
        subparser.add_argument("filename", help="File to open", default="")
        subparser.add_argument("--restarted", action="store_true")

    @classmethod
    def handle_commandline_args(cls, args):
        app_window_shown.connect(
            partial(cls._open_arg_file, arg_file=args.filename),
            weak=False,
            sender=app_window_shown.ANY,
        )

    @staticmethod
    def _open_arg_file(sender, arg_file):
        if os.path.isfile(arg_file):
            log.info(f"The application was invoked with a file: {arg_file}")
            uri = DocumentUri.from_filename(arg_file)
            wx.GetApp().mainFrame.open_uri(uri)
        elif DocumentUri.is_bookworm_uri(arg_file):
            uri = DocumentUri.from_uri_string(arg_file)
            log.info(f"The application was invoked with a uri: {uri}")
            wx.GetApp().mainFrame.open_uri(uri)
        else:
            try:
                uri = DocumentUri.from_base64_encoded_string(arg_file)
            except:
                log.exception(f"Invalid or unknown document uri: {arg_file}")
            else:
                wx.GetApp().mainFrame.open_uri(uri)


@register_subcommand
class ShellSubcommandHandler(BaseSubcommandHandler):
    subcommand_name = "shell"

    launcher_actions = {
        "shell_integrate": shell_integrate,
        "shell_disintegrate": shell_disintegrate,
        "setup_file_assoc": show_file_association_dialog,
    }

    @classmethod
    def add_arguments(cls, subparser):
        if (
            CURRENT_PACKAGING_MODE is not PackagingMode.Source
            and not IS_RUNNING_PORTABLE
        ):
            subparser.add_argument("--shell-integrate", action="store_true")
            subparser.add_argument("--shell-disintegrate", action="store_true")
            subparser.add_argument("--setup-file-assoc", action="store_true")

    @classmethod
    def handle_commandline_args(cls, args):
        for flag, func in cls.launcher_actions.items():
            flag_value = getattr(args, flag, None)
            if flag_value:
                func()
        return 0


@register_subcommand
class BenchmarkSubcommandHandler(BaseSubcommandHandler):
    subcommand_name = "benchmark"

    @classmethod
    def add_arguments(cls, subparser):
        subparser.add_argument("filename", help="File to open", default="")

    @classmethod
    def handle_commandline_args(cls, args):
        reader_page_changed.connect(
            lambda sender, current, prev: sys.exit(0),
            sender=reader_page_changed.ANY,
            weak=False,
        )
        return LauncherSubcommandHandler.handle_commandline_args(args)


class BookwormApp(wx.App):
    """The application class."""

    def OnInit(self):
        self.Bind(wx.EVT_END_SESSION, self.onEndSession)
        return True

    def InitLocale(self):
        pass

    def OnAssert(self, file, line, cond, msg):
        message = f"{file}, line {line}:\nassert {cond}: {msg}"
        log.warning(message, codepath="wx", stack_info=True)

    def onEndSession(self, event):
        app_shuttingdown.send(self)
        return self.OnExit()

    def OnExit(self):
        return appinfo.exit_code


def setupSubsystems():
    log.debug("Setting up application subsystems.")
    log.debug("Setting up the configuration subsystem.")
    setup_config()
    log.debug("Setting up the internationalization subsystem.")
    setup_i18n()
    log.debug("Initializing the database subsystem.")
    init_database()


def log_diagnostic_info():
    log.info("Starting Bookworm.")
    log.info(f"Bookworm Version: {appinfo.version}")
    log.info(f"Python version: {sys.version}")
    log.info(f"Platform: {platform.platform()}")
    log.info(f"OS description: {wx.GetOsDescription()}")
    log.info(f"Application architecture: {appinfo.arch}")
    if CURRENT_PACKAGING_MODE is PackagingMode.Portable:
        log.info("Running a portable copy of Bookworm.")
    elif CURRENT_PACKAGING_MODE is PackagingMode.Installed:
        log.info("Running an installed copy of Bookworm.")
    elif CURRENT_PACKAGING_MODE is PackagingMode.Source:
        log.info("Running Bookworm from source.")


def init_app_and_run_main_loop():
    appinfo.command_line_mode = True
    should_exit_early = handle_app_commandline_args()
    if should_exit_early is not None:
        log.debug("Exiting application after commandline handling")
        appinfo.exit_code = int(should_exit_early)
        return
    appinfo.command_line_mode = False

    if IS_IN_MAIN_PROCESS or not appinfo.is_frozen:
        configure_logger()
    log_diagnostic_info()
    if appinfo.args.debug or os.getenv("BOOKWORM_DEBUG"):
        appinfo.debug = True
    log.info(f"Debug mode is {'on' if appinfo.debug else 'off'}.")

    # Perform app initialization
    app_starting.send()
    wxlogfilename = logs_path("wx.log")
    app = BookwormApp(
        redirect=True, useBestVisual=True, filename=os.fspath(wxlogfilename)
    )
    if CURRENT_PACKAGING_MODE is PackagingMode.Source:
        app.RestoreStdio()
    setupSubsystems()
    mainFrame = app.mainFrame = BookViewerWindow(None, appinfo.display_name)
    app.service_handler = ServiceHandler(mainFrame)
    app.service_handler.register_builtin_services()

    mainFrame.finalize_gui_creation()
    app_started.send(app)
    log.info("The application has started successfully.")

    log.info("Preparing to show the application GUI.")
    app.SetTopWindow(mainFrame)
    mainFrame.Show(True)
    app_window_shown.send(mainFrame)
    app.MainLoop()
    log.info("Shutting down the application.")
    app_shuttingdown.send(app)


def run():
    try:
        init_app_and_run_main_loop()
        active_child_processes = "\n".join(
            p.name for p in multiprocessing.active_children()
        ).strip()
        if active_child_processes:
            log.debug(f"Active child processes: {active_child_processes}")
        log.info("The application has exited gracefully.")
        return appinfo.exit_code
    except Exception as e:
        log.critical("An unhandled error has occurred.", exc_info=True)
        raise e
