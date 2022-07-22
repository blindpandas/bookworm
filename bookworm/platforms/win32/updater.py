# coding: utf-8

import os
import shutil
import sys
import tempfile
import zipfile
from contextlib import suppress
from functools import partial
from hashlib import sha1
from pathlib import Path

import win32api
import win32con
import win32pdhutil
import wx
from requests.exceptions import RequestException


from bookworm import app, config, paths
from bookworm.commandline_handler import BaseSubcommandHandler, register_subcommand
from bookworm.gui.components import RobustProgressDialog, SnakDialog
from bookworm.http_tools import HttpResource
from bookworm.logger import logger
from bookworm.utils import generate_sha1hash

log = logger.getChild(__name__)


@register_subcommand
class KillOtherInstancesSubcommand(BaseSubcommandHandler):
    subcommand_name = "kill-other-instances"

    @classmethod
    def add_arguments(cls, subparser):
        pass

    @classmethod
    def handle_commandline_args(cls, args):
        kill_other_running_instances()
        return 0


def kill_other_running_instances():
    """Ensure that only this instance is running."""
    log.debug("Killing other running instances of the application.")
    with suppress(Exception):
        win32pdhutil.GetPerformanceAttributes("Process", "ID Process", app.name)
    pids = win32pdhutil.FindPerformanceAttributesByName(app.name)
    if (this_pid := win32api.GetCurrentProcessId()) in pids:
        pids.remove(this_pid)
    for pid in pids:
        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
        win32api.TerminateProcess(handle, 0)
        win32api.CloseHandle(handle)
        log.info(f"Killed other process with PID: {pid}")


def extract_update_bundle(bundle):
    past_update_dir = paths.data_path("update")
    if past_update_dir.exists():
        log.info("Found previous update data. Removing...")
        shutil.rmtree(past_update_dir, ignore_errors=True)
    log.debug("Extracting update bundle")
    extraction_dir = paths.data_path("update", "extracted")
    extraction_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle, compression=zipfile.ZIP_LZMA) as archive:
        archive.extractall(extraction_dir)
    return extraction_dir


def perform_update(upstream_version_info):
    msg = wx.MessageBox(
        # Translators: the content of a message indicating the availability of an update
        _(
            "A new update for Bookworm has been released.\n"
            "Would you like to download and install it?\n"
            "Installed Version: {current}\n"
            "New Version: {new}\n"
        ).format(current=app.version, new=upstream_version_info.version),
        # Translators: the title of a message indicating the availability of an update
        _("Bookworm Update"),
        style=wx.YES_NO | wx.ICON_INFORMATION,
    )
    if msg != wx.YES:
        log.info("User cancelled the update.")
        return
    # Download the update package
    progress_dlg = RobustProgressDialog(
        wx.GetApp().mainFrame,
        # Translators: the title of a message indicating the progress of downloading an update
        _("Downloading Update"),
        # Translators: a message indicating the progress of downloading an update bundle
        "{} {}".format(_("Downloading update bundle"), "".ljust(25)),
        maxvalue=101,
        can_hide=True,
        can_abort=True,
    )
    bundle_file = tempfile.TemporaryFile()
    try:
        log.debug(
            f"Downloading update from: {upstream_version_info.bundle_download_url}"
        )
        dl_request = HttpResource(upstream_version_info.bundle_download_url).download()
        callback = partial(file_download_callback, progress_dlg)
        progress_dlg.set_abort_callback(dl_request.cancel)
        dl_request.download_to_file(bundle_file, callback)
    except ConnectionError:
        log.exception("Failed to download update file", exc_info=True)
        progress_dlg.Dismiss()
        wx.CallAfter(
            wx.MessageBox,
            # Translators: the content of a message indicating a failure in downloading an update
            _(
                "A network error was occured when trying to download the update.\n"
                "Make sure you are connected to the internet, "
                "or try again at a later time."
            ),
            # Translators: the title of a message indicating a failure in downloading an update
            _("Network Error"),
            style=wx.ICON_ERROR,
        )
        return
    if progress_dlg.WasCancelled():
        log.debug("User canceled the download of the update.")
        return
    log.debug("The update bundle has been downloaded successfully.")
    if generate_sha1hash(bundle_file) != upstream_version_info.update_sha1hash:
        log.debug("Hashes do not match.")
        progress_dlg.Dismiss()
        bundle_file.close()
        msg = wx.MessageBox(
            # Translators: the content of a message indicating a corrupted file
            _(
                "The update file has been downloaded, but it has been corrupted during download.\n"
                "Would you like to download the update file again?"
            ),
            # Translators: the title of a message indicating a corrupted file
            _("Download Error"),
            style=wx.YES_NO | wx.ICON_QUESTION,
        )
        if msg == wx.YES:
            return perform_update(upstream_version_info)
        else:
            return
    # Go ahead and install the update
    log.debug("Installing the update...")
    bundle_file.seek(0)
    try:
        with progress_dlg.PulseContinuously(_("Extracting update bundle...")):
            extraction_dir = extract_update_bundle(bundle_file)
    except:
        log.debug("Error extracting update bundle.", exc_info=True)
        wx.MessageBox(
            _(
                "A problem has occured when installing the update.\nPlease check the logs for more info."
            ),
            _("Error installing update"),
            style=wx.ICON_ERROR,
        )
        return
    finally:
        bundle_file.close()
        progress_dlg.Dismiss()
    wx.MessageBox(
        # Translators: the content of a message indicating successful download of the update bundle
        _(
            "The update has been downloaded successfully, and it is ready to be installed.\n"
            "The application will be restarted in order to complete the update process.\n"
            "Click the OK button to continue."
        ),
        # Translators: the title of a message indicating successful download of the update bundle
        _("Download Completed"),
        style=wx.ICON_INFORMATION,
    )
    wx.CallAfter(execute_bootstrap, extraction_dir)


def execute_bootstrap(extraction_dir):
    log.info("Executing bootstrap to complete update.")
    move_to = extraction_dir.parent
    shutil.move(str(extraction_dir / "bootstrap.exe"), str(move_to))
    args = f'"{os.getpid()}" "{extraction_dir}" "{paths.app_path()}" "{sys.executable}"'
    viewer = wx.GetApp().mainFrame
    if viewer.reader.ready:
        viewer.reader.save_current_position()
    kill_other_running_instances()
    win32api.ShellExecute(0, "open", str(move_to / "bootstrap.exe"), args, "", 5)
    log.info("Bootstrap has been executed.")
    sys.exit(0)


def file_download_callback(progress_dlg, progress_value):
    progress_dlg.Update(
        progress_value.percentage,
        _("Downloaded {downloaded} MB of {total} MB").format(
            downloaded=progress_value.downloaded_mb, total=progress_value.total_mb
        ),
    )
