# coding: utf-8

import uuid
from copy import deepcopy
from pathlib import Path
from configobj import ConfigObj, ConfigObjError, ParseError
from validate import Validator, ValidateError
from bookworm import app
from bookworm.paths import config_path
from bookworm.concurrency import call_threaded
from bookworm.logger import logger
from .spec import config_spec, builtin_voice_profiles


log = logger.getChild(__name__)


# The configuration singleton
conf = None


class ConfigProvider:
    """Handles app configurations."""

    __slots__ = [
        "_profile_path",
        "profiles",
        "active_profile",
        "spec",
        "config",
        "validator",
    ]

    def __init__(self):
        self._profile_path = Path(config_path()) / "voice_profiles"
        self.profiles = {}
        self.active_profile = None
        self.spec = ConfigObj(
            config_spec, encoding="UTF8", list_values=False, _inspec=True
        )
        self.validator = Validator()
        self._init_config()
        if not self._profile_path.exists():
            self._profile_path.mkdir(parents=True)
            self._add_builtin_voice_profiles()
        self.list_voice_profiles()

    def _init_config(self):
        config_file = Path(config_path(f"{app.name}.ini"))
        try:
            self.config = ConfigObj(
                infile=str(config_file),
                configspec=self.spec,
                create_empty=True,
                encoding="UTF8",
            )
        except ConfigObjError:
            config_file.unlink()
            self.init_config()
        validated = self.config.validate(self.validator, copy=True)
        if validated == True:
            self.config.write()
        else:
            self.config.restore_defaults()
            self.config.write()

    def list_voice_profiles(self):
        self.profiles.clear()
        if not self._profile_path.exists():
            self._profile_path.mkdir()
        for file in self._profile_path.iterdir():
            if file.suffix != ".ini":
                continue
            try:
                profile = self.load_voice_profile(str(file))
            except ConfigObjError:
                continue
            self.profiles[profile["name"]] = profile

    def create_voice_profile(self, name):
        if name in self.profiles:
            raise ValueError(f"A profile with the name {name} already exists.")
        filetoken = uuid.uuid5(uuid.NAMESPACE_X500, name)
        filename = self._profile_path / f"{filetoken}.ini"
        profile = self.load_voice_profile(str(filename))
        profile["name"] = name
        profile.write()
        return profile

    def load_voice_profile(self, filename):
        newspec = ConfigObj()
        newspec["name"] = 'string(default="")'
        newspec["speech"] = deepcopy(self.spec["speech"])
        profile = ConfigObj(
            infile=filename, configspec=newspec, create_empty=True, encoding="UTF8"
        )
        validated = profile.validate(self.validator)
        if validated:
            profile.write()
        return profile

    def delete_voice_profile(self, name):
        if name not in self.profiles:
            raise ValueError(f"Profile {name} does not exists.")
        profile_path = Path(self.profiles[name].filename)
        profile_path.unlink()

    @call_threaded
    def _add_builtin_voice_profiles(self):
        for pname, pdata in builtin_voice_profiles:
            profile = self.create_voice_profile(pname)
            profile["speech"].update(pdata)
            profile.write()

    def __getitem__(self, key):
        if key == "speech" and self.active_profile is not None:
            return self.active_profile[key]
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value


def setup_config():
    global conf
    conf = ConfigProvider()


def save():
    global conf
    if conf:
        conf.config.write()
        for profile in conf.profiles.values():
            profile.write()
