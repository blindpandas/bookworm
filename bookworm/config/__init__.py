import os
from configobj import ConfigObj, ParseError
from validate import Validator, ValidateError
from .. import paths
from .spec import config_spec


conf = None

class ConfigLoadError(Exception):
    pass


def setup_config(copy=True, *args, **kwargs):
    global conf
    spec = ConfigObj(config_spec, encoding="UTF8", list_values=False, _inspec=True)
    try:
        config = ConfigObj(
            infile=paths.config_path("book-reader.ini"),
            configspec=spec,
            create_empty=True,
            encoding="UTF8",
            *args,
            **kwargs
        )
    except ParseError:
        raise ConfigLoadError("Unable to load %r" % config_path)
    validator = Validator()
    validated = config.validate(validator, copy=copy)
    if validated == True:
        config.write()
        conf = config
