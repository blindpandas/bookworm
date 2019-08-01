# coding: utf-8

"""Over the air update (OTAU) functionality."""

import sys
import os
import shutil
import zipfile
import tempfile
import wx
import win32api
import ujson as json
from io import BytesIO
from urllib.request import urlopen
from urllib.error import URLError
from hashlib import sha1
from pathlib import Path
from lzma import decompress
from bookworm import app
from bookworm import paths
from bookworm.concurrency import call_threaded
from bookworm.utils import generate_sha1hash
from bookworm.signals import app_started
from bookworm.logger import logger


log = logger.getChild(__name__)


def extract_update_bundle(bundle):
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


@app_started.connect
def _check_for_updates_upon_startup(sender):
    check_for_updates()


def parse_update_info(update_info):
    current_version = app.get_version_info()
    update_channel = current_version["pre_type"] or ""
    if update_channel not in update_info:
        return False, None, None
    upstream_version = update_info[update_channel]
    dl_url = upstream_version[f"{app.arch}_download"]
    dl_sha1hash = upstream_version[f"{app.arch}_sha1hash"]
    return upstream_version["version"], dl_url, dl_sha1hash


@call_threaded
def check_for_updates(verbose=False):
    past_update_dir = paths.data_path("update")
    if past_update_dir.exists():
        log.info("Found previous update data. Removing...")
        shutil.rmtree(past_update_dir, ignore_errors=True)
    log.info("Checking for updates...")
    try:
        content = urlopen(app.update_url)
    except URLError as e:
        log.error(f"Failed to check for updates. {e.args}")
        if verbose:
            wx.CallAfter(
                wx.MessageBox,
                "We couldn't access the internet right now. Please try again later.",
                "Network Error",
                style=wx.ICON_WARNING
            )
        return
    try:
        update_info = json.loads(content.read())
    except ValueError as e:
        log.error(f"Invalid content recieved. {e.args}")
        if verbose:
            wx.CallAfter(
                wx.MessageBox,
                "We have faced a technical problem while checking for updates. Please try again later.",
                "Error Checking For Updates",
                style=wx.ICON_WARNING
            )
        return
    upstream_version, dl_url, dl_sha1hash = parse_update_info(update_info)
    if not upstream_version or (upstream_version == app.version):
        log.info("No new version.")
        if verbose:
            wx.CallAfter(
                wx.MessageBox,
                "Congratulations, you have already got the latest version of Bookworm.\n"
                "We are working day and night on making Bookworm better. The next version "
                "of Bookworm is on its way, so wait for it. Rest assured, "
                "we will notify you when it is released.",
                "No Update",
                style=wx.ICON_INFORMATION
            )
        return
    # A new version is available
    log.debug(f"A new version is available. Version {upstream_version}")
    msg = wx.MessageBox(
        "A new update for Bookworm has been released.\n"
        "Would you like to download and install it?\n"
        f"\tInstalled Version: {app.version}\n"
        f"\tNew Version: {upstream_version}\n",
        "Update Available",
        style=wx.YES_NO|wx.ICON_INFORMATION
    )
    if msg == wx.YES:
        perform_update(dl_url, dl_sha1hash)


def perform_update(update_url, sha1hash):
    try:
        log.debug(f"Downloading update from: {update_url}")
        update_file = urlopen(update_url)
    except URLError as e:
        log.info(f"Faild to obtain the update file. {e.args}")
        wx.CallAfter(
            wx.MessageBox,
            "A network error was occured when trying to download the update.\n"
            "Make sure you are connected to the internet, "
            "or try again at a later time.",
            "Network Error",
            style=wx.ICON_ERROR
        )
        return
    update_file_size = update_file.length
    dlg = wx.ProgressDialog(
        "Downloading Update",
        f"Downloading {update_url}:",
        parent=wx.GetApp().mainFrame,
        maximum=update_file_size,
        style=wx.PD_APP_MODAL | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE,
    )
    bundle = tempfile.SpooledTemporaryFile(max_size=1024 * 30 * 1000)
    update_progress = lambda c, t=update_file_size: f"Downloading update. {round(c/(1024**2))} MB of {round(t/(1024**2))} MB"
    for chunk in update_file:
        bundle.write(chunk)
        downloaded = bundle.tell()
        dlg.Update(downloaded, update_progress(downloaded))
    wx.CallAfter(dlg.Hide)
    wx.CallAfter(dlg.Destroy)
    log.debug("The update bundle has been downloaded successfully.")
    if generate_sha1hash(bundle) != sha1hash:
        log.debug("Hashes do not match.")
        bundle.close()
        msg = wx.MessageBox(
            "The update file has been downloaded, but it has been corrupted during download.\n"
            "Would you like to download the update file again?",
            "Download Error",
            style=wx.YES_NO|wx.ICON_QUESTION
        )
        if msg == wx.YES:
            return perform_update(update_url, sha1hash)
        else:
            return
    # Go ahead and install the update
    log.debug("Installing the update...")
    wx.CallAfter(
        wx.MessageBox,
        "The update has been downloaded successfully, and it is ready to be installed.\nClick the OK button to install it now.",
        "Download Completed",
        style=wx.ICON_INFORMATION
    )
    extraction_dir = extract_update_bundle(bundle)
    bundle.close()
    wx.CallAfter(execute_bootstrap, extraction_dir)


def execute_bootstrap(extraction_dir):
    log.info("Executing bootstrap to complete update.")
    move_to = extraction_dir.parent
    shutil.move(str(extraction_dir / "bootstrap.exe"), str(move_to))
    args = f'"{os.getpid()}" "{extraction_dir}" "{paths.app_path()}" "{sys.executable}"'
    viewer = wx.GetApp().mainFrame
    if viewer.reader.ready:
        viewer.reader.save_current_position()
    win32api.ShellExecute(0, "open", str(move_to / "bootstrap.exe"), args, "", 5)
    log.info("Bootstrap has been executed.")
    sys.exit()
