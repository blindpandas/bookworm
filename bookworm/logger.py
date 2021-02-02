# coding: utf-8

import sys
import logging
from logging.handlers import RotatingFileHandler
from bookworm import paths
from bookworm import app


APP_LOG_FILE = f"{app.name}.log"
ERROR_LOG_FILE = "error.log"
MESSAGE_FORMAT = "%(asctime)s %(name)s %(levelname)s: %(message)s"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

formatter = logging.Formatter(MESSAGE_FORMAT, datefmt=DATE_FORMAT)
bookworm_filter = logging.Filter("bookworm")

logger = logging.getLogger("bookworm")
logger.setLevel(logging.DEBUG)

# handlers

app_handler = RotatingFileHandler(paths.logs_path(APP_LOG_FILE), mode="w")
app_handler.setFormatter(formatter)
app_handler.setLevel(logging.DEBUG)
logger.addHandler(app_handler)

error_handler = logging.FileHandler(paths.logs_path(ERROR_LOG_FILE), mode="w")
error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)
logger.addHandler(error_handler)
