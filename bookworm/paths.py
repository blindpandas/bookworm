# coding: utf-8

import logging
import platform
import bookworm
from pathlib import Path
from platform_utils import paths as path_finder
from functools import wraps
from bookworm import app
from bookworm.runtime import CURRENT_PACKAGING_MODE, PackagingMode


log = logging.getLogger("bookworm.paths")

# The appdata path when running from source
DATA_PATH_SOURCE = Path(bookworm.__path__[0]).parent / ".appdata"


def merge_paths(func):
    @wraps(func)
    def merge_paths_wrapper(*a):
        return func().joinpath(*a)

    return merge_paths_wrapper


@merge_paths
def data_path():
    if CURRENT_PACKAGING_MODE is PackagingMode.Installed:
        data_path = Path(path_finder.app_data_path(app.name))
    elif CURRENT_PACKAGING_MODE is PackagingMode.Portable:
        data_path = app_path("user-config")
    else:
        data_path = DATA_PATH_SOURCE
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
    return data_path


@merge_paths
def app_path():
    if CURRENT_PACKAGING_MODE in (PackagingMode.Installed, PackagingMode.Portable):
        return Path(path_finder.app_path())
    else:
        import bookworm

        return Path(bookworm.__path__[0])


@merge_paths
def config_path():
    path = data_path("config")
    if not path.exists():
        log.debug("%s path does not exist, creating..." % (path,))
        path.mkdir(parents=True, exist_ok=True)
    return path


@merge_paths
def logs_path():
    path = data_path("logs")
    if not path.exists():
        log.debug("%s path does not exist, creating..." % (path,))
        path.mkdir(parents=True, exist_ok=True)
    return path


@merge_paths
def locale_path():
    return app_path("resources", "locale")


@merge_paths
def db_path():
    path = data_path("database")
    if not path.exists():
        log.debug("%s path does not exist, creating..." % (path,))
        path.mkdir(parents=True, exist_ok=True)
    return path


@merge_paths
def docs_path():
    path = app_path("resources", "docs")
    if not path.exists():
        log.warning(f"Documentation files was not found in {path}. Folder not Found.")
    return path


@merge_paths
def home_data_path():
    if CURRENT_PACKAGING_MODE is PackagingMode.Installed:
        path = Path.home() / f".{app.name}"
    elif CURRENT_PACKAGING_MODE is PackagingMode.Portable:
        path = data_path(".saved_data")
    else:
        path = DATA_PATH_SOURCE / "home_data"
    if not path.exists():
        log.debug("%s path does not exist, creating..." % (path,))
        path.mkdir(parents=True, exist_ok=True)
    return path
