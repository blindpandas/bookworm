# coding: utf-8

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
from bookworm.utils import _gen_sha1hash
from bookworm.signals import app_started
from bookworm.logger import logger


log = logger.getChild(__name__)


def extract_update_bundle(bundle_filename):
    log.debug("Extracting update bundle")
    extraction_dir = paths.data_path("update", "extracted")
    if not extraction_dir.exists():
        extraction_dir.mkdir(parents=True, exist_ok=True)
    else:
        shutil.rmtree(extraction_dir)
    with open(bundle_filename, "rb") as bundle:
        archive_file = BytesIO(decompress(bundle.read()))
    with zipfile.ZipFile(archive_file) as archive:
        archive.extractall(extraction_dir)
    return extraction_dir


@app_started.connect
@call_threaded
def check_for_updates(verbose=False):
    past_update_dir = paths.data_path("update")
    if past_update_dir.exists():
        log.info("Found previous update data. Removing...")
        shutil.rmtree(past_update_dir, ignore_errors=True)
    log.info("Checking for updates...")
    current_version = app.version
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
    if update_info["version"] == app.version:
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
    log.debug(f"A new version is available. Version {update_info['version']}")
    msg = wx.MessageBox(
        "A new update for Bookworm has been released.\n"
        "Would you like to download and install it?\n"
        f"\tInstalled Version: {app.version}\n"
        f"\tNew Version: {update_info['version']}\n"
        f"\tRelease Date: {update_info['release_date']}",
        "Update Available",
        style=wx.YES_NO|wx.ICON_INFORMATION
    )
    if msg == wx.YES:
        perform_update(update_info[f"{app.arch}_download"], update_info[f"{app.arch}_sha1hash"])


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
    bundle = tempfile.NamedTemporaryFile()
    log.debug(f"Downloading update bundle to {bundle.name}")
    for chunk in update_file:
        bundle.write(chunk)
        dlg.Update(bundle.tell(), "Downloading Update...")
    wx.CallAfter(dlg.Hide)
    wx.CallAfter(dlg.Destroy)
    log.debug("Update downloaded successfully.")
    bundle_hash = _gen_sha1hash(bundle.name)
    if bundle_hash != sha1hash:
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
        "The update has been downloaded successfully, and it is ready to be installed.",
        "Download Completed",
        style=wx.ICON_INFORMATION
    )
    extraction_dir = extract_update_bundle(bundle.name)
    bundle.close()
    execute_bootstrap(extraction_dir)


def execute_bootstrap(extraction_dir):
    log.info("Executing bootstrap to complete update.")
    move_to = extraction_dir.parent
    shutil.move(Path(extraction_dir.name) / "bootstrap.exe", move_to)
    args = [f'"{os.getpid()}"', f'"{extraction_dir}"', f'"{paths.app_path()}"', sys.executable]
    viewer = wx.GetApp().mainFrame
    if viewer.reader.ready:
        viewer.reader.save_current_position()
        args[-1] += f' --filename "{viewer.reader.document.filename}"'
    if app.debug:
        args[-1] += " --debug"
    args[-1] = f'"{args[-1]}"'
    args = " ".join(args)
    win32api.ShellExecute(0, "open", str(move_to / "bootstrap.exe"), args, "", 5)
