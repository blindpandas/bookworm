# coding: utf-8

import logging
from logging.handlers import RotatingFileHandler
from bookworm import paths
from bookworm import app
from bookworm.runtime import IS_IN_MAIN_PROCESS


APP_LOG_FILE = app.name
ERROR_LOG_FILE = "error"
MESSAGE_FORMAT = "%(levelname)s - %(name)s - %(asctime)s - %(threadName)s (%(thread)d):\n%(message)s"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
formatter = logging.Formatter(MESSAGE_FORMAT, datefmt=DATE_FORMAT)
BOOKWORM_FILTER = logging.Filter('bookworm')

logger = logging.getLogger("bookworm")
logger.setLevel(logging.DEBUG)



def configure_logger(log_file_suffix=""):
    suffix = log_file_suffix  if not log_file_suffix  else '.' + log_file_suffix 
    app_handler = RotatingFileHandler(paths.logs_path(f"{APP_LOG_FILE}{suffix}.log"), mode="w")
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.DEBUG)
    app_handler.addFilter(BOOKWORM_FILTER)
    logger.addHandler(app_handler)

    error_handler = logging.FileHandler(paths.logs_path(f"{ERROR_LOG_FILE}{suffix}.log"), mode="w")
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

