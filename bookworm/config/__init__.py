# coding: utf-8

from pathlib import Path
from configobj import ConfigObj, ConfigObjError, ParseError
from validate import Validator, ValidateError
from bookworm import app
from bookworm.paths import config_path
from bookworm.concurrency import call_threaded
from bookworm.logger import logger
from .spec import config_spec


log = logger.getChild(__name__)


# The configuration singleton
conf = None


class ConfigProvider:
    """Handles app configurations."""

    __slots__ = ["spec", "config", "validator"]

    def __init__(self):
        self.spec = ConfigObj(
            config_spec, encoding="UTF8", list_values=False, _inspec=True
        )
        self.validator = Validator()
        self.validate_and_write()

    def validate_and_write(self):
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

    def __getitem__(self, key):
        return self.config[key]


def setup_config():
    global conf
    conf = ConfigProvider()


def save():
    global conf
    if conf:
        conf.config.write()
