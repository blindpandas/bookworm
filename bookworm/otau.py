# coding: utf-8

import time
from typing import Tuple

import wx
from pydantic import BaseModel, HttpUrl, RootModel, field_validator
from packaging import version

from bookworm import app, config
from bookworm import typehints as t
from bookworm import updater
from bookworm.concurrency import call_threaded
from bookworm.http_tools import RemoteJsonResource
from bookworm.logger import logger
from bookworm.service import BookwormService

log = logger.getChild(__name__)
# Update check interval (in seconds)
UPDATE_CHECK_INTERVAL = 20 * 60 * 60


class UpdateChannel(RootModel[str]):
    root: str

    def __hash__(self):
        return hash(self.root)

    @field_validator("root")
    @classmethod
    def validate_identifier(cls, v: str):
        if v is None:
            v = ""
        if v not in ["", "b", "a", "rc"]:
            raise TypeError("Unrecognized release identifier")
        return v

    @property
    def is_major(self) -> bool:
        return self.root == ""


class VersionInfo(BaseModel):
    version: str
    x86_download: HttpUrl
    x64_download: HttpUrl
    x86_sha1hash: str
    x64_sha1hash: str

    @property
    def bundle_download_url(self) -> HttpUrl:
        return getattr(self, f"{app.arch}_download")

    @property
    def update_sha1hash(self) -> str:
        return getattr(self, f"{app.arch}_sha1hash")


class UpdateInfo(RootModel[t.Dict[UpdateChannel, VersionInfo]]):
    root: t.Dict[UpdateChannel, VersionInfo]

    @property
    def channels(self) -> Tuple[UpdateChannel]:
        return tuple(self.root.keys())

    def get_update_info_for_channel(self, channel_identifier: str) -> VersionInfo:
        if channel_identifier is None:
            channel_identifier = ""
        return self.root.get(UpdateChannel.model_validate(channel_identifier))


def is_newer_version(current_version: str, upstream_version: str) -> bool:
    """Compare two version strings to determine if upstream_version is newer than current_version.

    Args:
        current_version: The version string of the current installation
        upstream_version: The version string of the available update

    Returns:
        bool: True if upstream_version is newer than current_version

    Note:
        - Returns False if upstream_version is invalid
        - Returns True if current_version is invalid but upstream_version is valid
        - Uses semantic versioning for valid version strings
    """
    # Normal version comparison
    try:
        return version.parse(upstream_version) > version.parse(current_version)
    except Exception:
        log.warning(
            f"Failed to parse version strings: current_version='{current_version}', "
            f"upstream_version='{upstream_version}'"
        )

        # Check if upstream version is valid
        try:
            version.parse(upstream_version)
        except Exception:
            return False  # Invalid upstream version is never newer

        # Check if current version is valid
        try:
            version.parse(current_version)
        except Exception:
            return True  # Valid upstream version is always newer than invalid current version


@call_threaded
def check_for_updates(verbose=False):
    log.info("Checking for updates...")
    try:
        update_info = RemoteJsonResource(url=app.update_url, model=UpdateInfo).get()
    except ConnectionError:
        log.exception("Failed to check for updates.", exc_info=True)
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
    except ValueError:
        log.exception("Invalid content recieved.", exc_info=True)
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
    # Precede with the update
    update_channel = app.get_version_info().get("pre_type", "")
    upstream_version_info = update_info.get_update_info_for_channel(update_channel)
    if (upstream_version_info is None) or (
        not is_newer_version(app.version, upstream_version_info.version)
    ):
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
    log.debug(f"A new version is available. Version {upstream_version_info.version}")
    updater.perform_update(upstream_version_info)


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
