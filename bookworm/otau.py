# coding: utf-8

import time
import wx
import requests
from requests.exceptions import RequestException
from bookworm import app
from bookworm import config
from bookworm.base_service import BookwormService
from bookworm.concurrency import call_threaded
from bookworm.platform_services import updater
from bookworm.utils import ignore
from bookworm.logger import logger


log = logger.getChild(__name__)

# Update check interval (in seconds)
UPDATE_CHECK_INTERVAL = 20 * 60 * 60


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
        config.conf["general"]["last_update_check"] = time.time()
        config.save()
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
    updater.perform_update(upstream_version, dl_url, dl_sha1hash)


class OTAUService(BookwormService):
    name = "otau"
    has_gui = True

    @classmethod
    def check(self):
        return app.is_frozen and not app.command_line_mode

    def __post_init__(self):
        self.check_for_updates_upon_startup()

    def process_menubar(self, menubar):
        checkForUpdatesMmenuItem = self.view.helpMenu.Insert(
            4,
            wx.ID_ANY,
            # Translators: the label of an item in the application menubar
            _("&Check for updates"),
            # Translators: the help text of an item in the application menubar
            _("Update the application"),
        )
        self.view.Bind(
            wx.EVT_MENU,
            lambda e: check_for_updates(verbose=True),
            checkForUpdatesMmenuItem,
        )

    def check_for_updates_upon_startup(self):
        _last_update_check = config.conf["general"]["last_update_check"]
        if (
            config.conf["general"]["auto_check_for_updates"]
            and (time.time() - _last_update_check) > UPDATE_CHECK_INTERVAL
        ):
            check_for_updates()
