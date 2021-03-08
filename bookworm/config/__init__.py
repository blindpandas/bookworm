# coding: utf-8

from pathlib import Path
from configobj import ConfigObj, ConfigObjError, flatten_errors
from configobj.validate import Validator
from bookworm import app
from bookworm.paths import config_path
from bookworm.logger import logger
from .spec import config_spec


log = logger.getChild(__name__)


# The configuration singleton
conf = None


class ConfigProvider:
    """Handles app configurations."""

    __slots__ = ["config_file", "spec", "config", "validator"]

    def __init__(self):
        self.config_file = str(Path(config_path(f"{app.name}.ini")))
        self.spec = ConfigObj(
            config_spec, encoding="UTF8", list_values=False, _inspec=True
        )
        self.validator = Validator()
        self.validate_and_write()

    def validate_and_write(self):
        try:
            self.config = ConfigObj(
                infile=self.config_file,
                configspec=self.spec,
                create_empty=True,
                encoding="UTF8",
            )
            self.config.filename = self.config_file
        except ConfigObjError:
            log.exception("Failed to initialize config", exc_info=True)
            Path(self.config_file).unlink()
            return self.validate_and_write()
        validated = self.config.validate(
            self.validator, copy=True, preserve_errors=True
        )
        if validated == True:
            self.config.write()
        else:
            log.error("Failed to validate config.")
            validation_errors = flatten_errors(self.config, validated)
            log.error(f"Configuration validation errors: {validation_errors}")
            self.config.restore_defaults()
            self.config.write()

    def __getitem__(self, key):
        return self.config[key]


def setup_config():
    global conf
    conf = ConfigProvider()


def save():
    global conf
    if conf is not None:
        conf.config.write()
