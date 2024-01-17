# coding: utf-8

from __future__ import annotations

import contextlib
import importlib
import hashlib
import os
import sys
import uuid
from functools import lru_cache, wraps
from pathlib import Path

import wx

from bookworm import app
from bookworm import typehints as t
from bookworm.concurrency import call_threaded
from bookworm.logger import logger

log = logger.getChild(__name__)


@contextlib.contextmanager
def switch_stdout(out):
    original_stdout = sys.stdout
    try:
        sys.stdout = out
        yield
    finally:
        sys.stdout = original_stdout


def mute_stdout():
    return switch_stdout(None)


def ignore(*exceptions, retval=None):
    """Execute function ignoring any one of the given exceptions if raised."""

    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if not any(isinstance(e, exc) for exc in exceptions):
                    raise
                log.exception(
                    f"Ignored exc `{e}` raised when executing function {func}",
                    exc_info=True,
                )
                return retval

        return wrapped

    return wrapper


def restart_application(*extra_args, debug=False, restore=True):
    from bookworm.commandline_handler import run_subcommand_in_a_new_process

    args = ["launcher", "--restarted"]
    if debug and ("--debug" not in args):
        args.insert(0, "--debug")
    reader = wx.GetApp().mainFrame.reader
    if restore and reader.ready:
        args.append(reader.document.uri.base64_encode())
        with contextlib.suppress(Exception):
            reader.save_current_position()
    else:
        args.append(os.devnull)
    wx.GetApp().ExitMainLoop()
    log.info(f"Restarting application with args: {args}")
    run_subcommand_in_a_new_process(args, hidden=False, detached=True)
    sys.exit(0)


def recursively_iterdir(path):
    """Iterate over files, exclusively, in path and its sub directories."""
    for item in Path(path).iterdir():
        if item.is_dir():
            yield from recursively_iterdir(item)
        else:
            yield item


def gui_thread_safe(func):
    """Always call the function in the gui thread."""

    @wraps(func)
    def wrapper(*a, **kw):
        return wx.CallAfter(func, *a, **kw)

    return wrapper


def generate_file_md5(filepath):
    hasher = hashlib.md5()
    for chunk in open(filepath, "rb"):
        hasher.update(chunk)
    return hasher.hexdigest()


def generate_sha1hash(content):
    hasher = hashlib.sha1()
    is_file_like = hasattr(content, "seek")
    if not is_file_like:
        file = open(content, "rb")
    else:
        content.seek(0)
        file = content
    for chunk in file:
        hasher.update(chunk)
    if not is_file_like:
        file.close()
    return hasher.hexdigest()


def random_uuid():
    return uuid.uuid4().hex


@call_threaded
def generate_sha1hash_async(filename):
    return generate_sha1hash(filename)


def format_datetime(
    datetime_to_format, format="medium", localized=True, date_only=False
) -> str:
    return app.current_language.format_datetime(
        datetime_to_format, date_only=date_only, format=format, localized=localized
    )


def lazy_module(mod: str):
    module = importlib.__import__(mod)
    return module
