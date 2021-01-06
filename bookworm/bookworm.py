# coding: utf-8

"""Make sure that runtime components are OK and run the app."""

import sys
from bookworm.platform_services import check_runtime_components


def main():
    try:
        check_runtime_components()
    except EnvironmentError:
        import wx

        wx.SafeShowMessage(
            "Unable To Start",
            "Bookworm is unable to start because some key components are missing from your system.\n"
            "Bookworm requires that the .NET Framework v4.0 or a later version is present in the target system.\n"
            "Head over to the following link to download and install the .NET Framework v4.0:\n"
            "https://www.microsoft.com/en-us/download/details.aspx?id=17718",
        )
        sys.exit(1)
    try:
        from bookworm import bootstrap

        bootstrap.run()
    except Exception as e:
        import logging
        import wx
        from pathlib import Path

        MESSAGE_FORMAT = "%(asctime)s %(name)s %(levelname)s: %(message)s"
        DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
        logfile = Path.home() / "Bookworm.errors.log"
        extern_file = logging.FileHandler(filename=logfile, mode="w")
        extern_file.setFormatter(logging.Formatter(MESSAGE_FORMAT, datefmt=DATE_FORMAT))
        logging.getLogger("").addHandler(extern_file)
        logging.debug("An error was occured while starting the application.")
        logging.critical("Error details:", exc_info=True)
        wx.SafeShowMessage(
            "Application Error",
            "Bookworm has faced some issues.\n"
            f"The error details has been written to the file:\n{logfile}",
        )
        sys.exit(1)
