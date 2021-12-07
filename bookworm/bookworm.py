# coding: utf-8

"""Make sure that runtime components are OK and run the app."""

import sys
import os
from bookworm import app
from bookworm.platform_services import check_runtime_components


def main():
    try:
        check_runtime_components()
    except EnvironmentError as e:
        import wx

        wx.SafeShowMessage("Unable To Start", e.args[0])
        sys.exit(1)
    try:
        from bookworm import bootstrap

        sys.exit(bootstrap.run())
    except Exception:
        import logging
        from pathlib import Path
        from bookworm import app

        MESSAGE_FORMAT = "%(asctime)s %(name)s %(levelname)s: %(message)s"
        DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
        logfile = Path.home() / "Bookworm.errors.log" if app.is_frozen else os.devnull
        extern_file = logging.FileHandler(filename=logfile, mode="w")
        extern_file.setFormatter(logging.Formatter(MESSAGE_FORMAT, datefmt=DATE_FORMAT))
        logging.getLogger("").addHandler(extern_file)
        logging.debug("An error was occurred while starting the application.")
        if app.is_frozen and not app.command_line_mode:
            import wx
            error_message = (
                "Bookworm has faced some issues.\n"
                f"The error details has been written to the file:\n{logfile}"
            )
            wx.SafeShowMessage(
                "Application Error",
                error_message
            )
        else:
            logging.error("Bookworm has faced some issues.\n")
        logging.critical("Error details:", exc_info=True)
        sys.exit(app.exit_code or 1)
