# coding: utf-8

"""Make sure that runtime components are OK and run the app."""

import logging
import os
import sys
from pathlib import Path

from bookworm import app


def report_fatal_error(
    *, title, message, exc_info=True, exit_code=1, log_file=None, show_gui=False
):
    MESSAGE_FORMAT = "%(asctime)s %(name)s %(levelname)s: %(message)s"
    DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
    logger = logging.getLogger("")
    logger.addHandler(logging.StreamHandler(sys.stderr))

    if log_file is not None:
        file_handler = logging.FileHandler(filename=log_file, mode="w")
        file_handler.setFormatter(
            logging.Formatter(MESSAGE_FORMAT, datefmt=DATE_FORMAT)
        )
        logger.addHandler(file_handler)

    logger.debug("An error was occurred while starting the application.")
    logger.fatal(title)
    logger.fatal(message)
    if exc_info:
        logger.exception("ERROR DETAILS:\n", exc_info=True)

    if show_gui:
        try:
            import wx

            wx.SafeShowMessage(title, message)
        except:
            logger.fatal("Failed to report error graphically")
    sys.exit(exit_code)


def main():
    try:
        from bookworm.platforms import check_runtime_components

        check_runtime_components()

        from bookworm import bootstrap

        sys.exit(bootstrap.run())
    except Exception as e:
        log_file = Path.home() / "bookworm.errors.log" if app.is_frozen else None
        message = "A fatal error has occured. Please check the log for more details."
        if log_file:
            message += f"\nThe log has been written to the file:\n{log_file}"
        report_fatal_error(
            title="Failed to start Bookworm",
            message=message,
            exc_info=True,
            log_file=log_file,
            show_gui=app.is_frozen,
            exit_code=app.exit_code or 1,
        )
