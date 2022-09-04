# coding: utf-8

import shutil
from pathlib import Path
from tempfile import TemporaryFile
from zipfile import ZipFile

import requests
import wx

from bookworm import app
from bookworm import typehints as t
from bookworm import pandoc
from bookworm.http_tools import HttpResource, RemoteJsonResource
from bookworm.logger import logger


log = logger.getChild(__name__)


BRANCH = "develop"
PANDOC_DOWNLOAD_URL = f"https://raw.githubusercontent.com/blindpandas/bookworm/{BRANCH}/packages/pandoc/pandoc_x64.zip"
PANDOC_VERSION_URL = f"https://raw.githubusercontent.com/blindpandas/bookworm/{BRANCH}/packages/pandoc/version"


def is_new_pandoc_version_available():
    remote_version = requests.get(PANDOC_VERSION_URL).text
    return pandoc.get_version() != remote_version


def download_pandoc(progress_dlg):
    pandoc_directory = pandoc.get_pandoc_path()
    callback = lambda prog: progress_dlg.Update(prog.percentage, prog.user_message)
    try:
        dl_request = HttpResource(PANDOC_DOWNLOAD_URL).download()
        progress_dlg.set_abort_callback(dl_request.cancel)
        with TemporaryFile() as dlfile:
            dl_request.download_to_file(dlfile, callback)
            if dl_request.is_cancelled():
                return
            with progress_dlg.PulseContinuously(_("Extracting file...")):
                with ZipFile(dlfile, "r") as zfile:
                    pandoc_directory.mkdir(parents=True, exist_ok=True)
                    zfile.extractall(path=pandoc_directory)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a message box
            _("Success"),
            # Translators: content of a messagebox
            _("Pandoc downloaded successfully"),
        )
        return True
    except ConnectionError:
        log.debug("Failed to download pandoc.", exc_info=True)
        wx.GetApp().mainFrame.notify_user(
            # Translators: title of a messagebox
            _("Connection Error"),
            _(
                "Could not download Pandoc.\nPlease check your internet connection and try again."
            ),
            icon=wx.ICON_ERROR,
        )
    except:
        log.exception(
            "An error occurred while adding Pandoc", exc_info=True
        )
        wx.GetApp().mainFrame.notify_user(
            _("Error"),
            _("Could not add Pandoc.\nPlease try again."),
            icon=wx.ICON_WARNING,
        )


def remove_pandoc():
    pandoc_directory = pandoc.get_pandoc_path()
    shutil.rmtree(pandoc_directory, ignore_errors=False)
