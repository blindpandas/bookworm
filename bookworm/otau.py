# coding: utf-8

"""Over the air update (OTAU) functionality."""

import sys
import os
import shutil
import zipfile
import tempfile
import requests
import wx
import win32api
from math import ceil
from io import BytesIO
from hashlib import sha1
from pathlib import Path
from lzma import decompress
from System.Diagnostics import Process
from requests.exceptions import RequestException
from bookworm import app
from bookworm import config
from bookworm import paths
from bookworm.concurrency import call_threaded
from bookworm.utils import ignore, generate_sha1hash
from bookworm.logger import logger


log = logger.getChild(__name__)


def kill_other_running_instances():
    """Ensure only one instance is running."""
    log.debug("Killing other running instances of the application.")
    pid, exe_dir = os.getpid(), Path(sys.executable).resolve().parent
    for proc in Process.GetProcessesByName(app.name):
        if Path(proc.MainModule.FileName).resolve().parent != exe_dir:
            continue
        if proc.Id != os.getpid():
            proc.Kill()


@ignore(OSError)
def extract_update_bundle(bundle):
    past_update_dir = paths.data_path("update")
    if past_update_dir.exists():
        log.info("Found previous update data. Removing...")
        shutil.rmtree(past_update_dir, ignore_errors=True)
    log.debug("Extracting update bundle")
    bundle.seek(0)
    extraction_dir = paths.data_path("update", "extracted")
    if extraction_dir.exists():
        shutil.rmtree(extraction_dir)
    extraction_dir.mkdir(parents=True, exist_ok=True)
    archive_file = BytesIO(decompress(bundle.read()))
    with zipfile.ZipFile(archive_file) as archive:
        archive.extractall(extraction_dir)
    return extraction_dir


def check_for_updates_upon_startup():
    if not app.command_line_mode and config.conf["general"]["auto_check_for_updates"]:
        check_for_updates()
    else:
        log.info("Automatic updates are disabled by user.")


@ignore(KeyError, retval=(None,) * 3)
def parse_update_info(update_info):
    current_version = app.get_version_info()
    update_channel = current_version["pre_type"] or ""
    upstream_version = update_info[update_channel]
    dl_url = upstream_version[f"{app.arch}_download"]
    dl_sha1hash = upstream_version[f"{app.arch}_sha1hash"]
    return upstream_version["version"], dl_url, dl_sha1hash


@call_threaded
def check_for_updates(verbose=False):
    log.info("Checking for updates...")
    try:
        version_info = response = requests.get(app.update_url)
        version_info.raise_for_status()
    except RequestException as e:
        log.error(f"Failed to check for updates. {e.args}")
        if verbose:
            wx.CallAfter(
                wx.MessageBox,
                # Translators: the content of a message indicating a connection error
                _("We couldn't access the internet right now. Please try again later."),
                # Translators: the title of a message indicating a connection error
                _("Network Error"),
                style=wx.ICON_WARNING,
            )
        return
    try:
        update_info = version_info.json()
    except ValueError as e:
        log.error(f"Invalid content recieved. {e.args}")
        if verbose:
            wx.CallAfter(
                wx.MessageBox,
                # Translators: the content of a message indicating an error while updating the app
                _(
                    "We have faced a technical problem while checking for updates. Please try again later."
                ),
                # Translators: the title of a message indicating an error while updating the app
                _("Error Checking For Updates"),
                style=wx.ICON_WARNING,
            )
        return
    upstream_version, dl_url, dl_sha1hash = parse_update_info(update_info)
    if not upstream_version or (upstream_version == app.version):
        log.info("No new version.")
        if verbose:
            wx.CallAfter(
                wx.MessageBox,
                # Translators: the content of a message indicating that there is no new version
                _(
                    "Congratulations, you have already got the latest version of Bookworm.\n"
                    "We are working day and night on making Bookworm better. The next version "
                    "of Bookworm is on its way, so wait for it. Rest assured, "
                    "we will notify you when it is released."
                ),
                # Translators: the title of a message indicating that there is no new version
                _("No Update"),
                style=wx.ICON_INFORMATION,
            )
        return
    # A new version is available
    log.debug(f"A new version is available. Version {upstream_version}")
    msg = wx.MessageBox(
        # Translators: the content of a message indicating the availability of an update
        _(
            "A new update for Bookworm has been released.\n"
            "Would you like to download and install it?\n"
            "\tInstalled Version: {current}\n"
            "\tNew Version: {new}\n"
        ).format(current=app.version, new=upstream_version),
        # Translators: the title of a message indicating the availability of an update
        _("Update Available"),
        style=wx.YES_NO | wx.ICON_INFORMATION,
    )
    if msg == wx.YES:
        perform_update(dl_url, dl_sha1hash)


def perform_update(update_url, sha1hash):
    try:
        log.debug(f"Downloading update from: {update_url}")
        update_file = requests.get(update_url, stream=True)
        update_file.raise_for_status()
    except RequestException as e:
        log.info(f"Faild to obtain the update file. {e.args}")
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
    update_file_size = int(update_file.headers.get('content-length', 20 * 1024 ** 2))
    dlg = wx.ProgressDialog(
        # Translators: the title of a message indicating the progress of downloading an update
        _("Downloading Update"),
        # Translators: a message indicating the progress of downloading an update bundle
        _("Downloading {url}:").format(url=update_url),
        parent=wx.GetApp().mainFrame,
        maximum=99,
        style=wx.PD_APP_MODAL | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE
    )
    bundle = tempfile.SpooledTemporaryFile(max_size=1024 * 30 * 1000)
    # Translators: a message indicating the progress of downloading an update bundle
    update_progress = lambda c, t=update_file_size: _(
        "Downloading. {downloaded} MB of {total} MB"
    ).format(downloaded=round(c / (1024 ** 2)), total=round(t / (1024 ** 2)))
    csize = ceil(update_file_size/100)
    for (progval, chunk) in enumerate(update_file.iter_content(chunk_size=csize)):
        bundle.write(chunk)
        downloaded = bundle.tell()
        wx.CallAfter(dlg.Update, progval, update_progress(downloaded))
    wx.CallAfter(dlg.Hide)
    wx.CallAfter(dlg.Destroy)
    log.debug("The update bundle has been downloaded successfully.")
    if generate_sha1hash(bundle) != sha1hash:
        log.debug("Hashes do not match.")
        bundle.close()
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
            return perform_update(update_url, sha1hash)
        else:
            return
    # Go ahead and install the update
    log.debug("Installing the update...")
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
    ex_dlg = wx.ProgressDialog(
        # Translators: the title of a message shown when extracting an update bundle
        _("Extracting Update Bundle"),
        # Translators: a message shown when extracting an update bundle
        _("Please wait..."),
        parent=wx.GetApp().mainFrame,
        style=wx.PD_APP_MODAL
    )
    extraction_dir = extract_update_bundle(bundle)
    bundle.close()
    wx.CallAfter(ex_dlg.Close)
    wx.CallAfter(ex_dlg.Destroy)
    if extraction_dir is not None:
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
