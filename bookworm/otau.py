# coding: utf-8

import time

import wx
from pydantic import BaseModel, HttpUrl, validator

from bookworm import app, config
from bookworm import typehints as t
from bookworm.concurrency import call_threaded
from bookworm.http_tools import RemoteJsonResource
from bookworm.logger import logger
from bookworm import updater
from bookworm.service import BookwormService

log = logger.getChild(__name__)
# Update check interval (in seconds)
UPDATE_CHECK_INTERVAL = 20 * 60 * 60


class UpdateChannel(BaseModel):
    __root__: str

    def __hash__(self):
        return hash(self.__root__)

    @validator("__root__")
    def validate_identifier(cls, v):
        if v not in ["", "b", "a", "dev"]:
            raise TypeError("Unrecognized release identifier")
        return v

    @property
    def is_major(self):
        return self.__root__ == ""


class VersionInfo(BaseModel):
    version: str
    x86_download: HttpUrl
    x64_download: HttpUrl
    x86_sha1hash: str
    x64_sha1hash: str

    @property
    def bundle_download_url(self):
        return getattr(self, f"{app.arch}_download")

    @property
    def update_sha1hash(self):
        return getattr(self, f"{app.arch}_sha1hash")


class UpdateInfo(BaseModel):
    __root__: t.Dict[UpdateChannel, VersionInfo]

    @property
    def channels(self):
        return tuple(self.__root__.keys())

    def get_update_info_for_channel(self, channel_identifier):
        return self.__root__.get(UpdateChannel.construct(__root__=channel_identifier))


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
        upstream_version_info.version == app.version
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
