# coding: utf-8

import multiprocessing
import logging
from logging.handlers import RotatingFileHandler
from bookworm import paths
from bookworm import app
from bookworm.runtime import IS_IN_MAIN_PROCESS


APP_LOG_FILE = app.name
ERROR_LOG_FILE = "error"
MESSAGE_FORMAT = "%(asctime)s %(name)s %(levelname)s: %(message)s"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

formatter = logging.Formatter(MESSAGE_FORMAT, datefmt=DATE_FORMAT)
bookworm_filter = logging.Filter("bookworm")


def configure_logger(logger, log_file_suffix=""):
    app_handler = RotatingFileHandler(paths.logs_path(f"{APP_LOG_FILE}{log_file_suffix}.log"), mode="w")
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.DEBUG)
    logger.addHandler(app_handler)

    error_handler = logging.FileHandler(paths.logs_path(f"{ERROR_LOG_FILE}{log_file_suffix}.log"), mode="w")
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)


logger = logging.getLogger("bookworm")
logger.setLevel(logging.DEBUG)


if  IS_IN_MAIN_PROCESS:
    configure_logger(logger)
