# coding: utf-8

import sys
import operator
import regex
import uuid
import wx
import hashlib
from contextlib import contextmanager, closing as contextlib_closing
from functools import wraps, lru_cache
from pathlib import Path
from xml.sax.saxutils import escape
from bookworm import typehints as t
from bookworm import app
from bookworm.concurrency import call_threaded
from bookworm.platform_services.runtime import system_start_app
from bookworm.logger import logger


log = logger.getChild(__name__)


# Taken from: https://stackoverflow.com/a/47248784
URL_REGEX = regex.compile(
    r"""(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))"""
)
URL_BAD_CHARS = "'\\.,[](){}:;\""


# New line character
UNIX_NEWLINE = "\n"
WINDOWS_NEWLINE = "\r\n"
MAC_NEWLINE = "\r"
NEWLINE = UNIX_NEWLINE
MORE_THAN_ONE_LINE = regex.compile(r"[\n]{2,}")
EXCESS_LINE_REPLACEMENT_FUNC = lambda m: m[0].replace("\n", " ")[:-1] + "\n"


@contextmanager
def switch_stdout(out):
    original_stdout = sys.stdout
    try:
        sys.stdout = out
        yield
    finally:
        sys.stdout = original_stdout


def mute_stdout():
    return switch_stdout(None)


def normalize_line_breaks(text, line_break=UNIX_NEWLINE):
    return text.replace("\r", " ")


def remove_excess_blank_lines(text):
    return MORE_THAN_ONE_LINE.sub(
        EXCESS_LINE_REPLACEMENT_FUNC, normalize_line_breaks(text)
    )


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
                    f"Ignored exc {e} raised when executing function {func}",
                    exc_info=True,
                )
                return retval

        return wrapped

    return wrapper


def restart_application(*extra_args, debug=False, restore=True):
    args = list(extra_args) + ["--restarted"]
    reader = wx.GetApp().mainFrame.reader
    if restore and reader.ready:
        args.insert(0, f"{reader.document.filename}")
        reader.save_current_position()
    if debug and ("--debug" not in args):
        args.append("--debug")
    wx.GetApp().ExitMainLoop()
    system_start_app(sys.executable, args)
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


def is_external_url(text):
    return URL_REGEX.match(text) is not None


@lru_cache(maxsize=5)
def get_url_spans(text):
    return tuple(
        (span := m.span(), text[slice(*span)].strip(URL_BAD_CHARS))
        for m in URL_REGEX.finditer(text)
    )


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


def format_datetime(date, format="medium", localized=True) -> str:
    return app.current_language.format_datetime(
        date, format=format, localized=localized
    )


def escape_html(text):
    """Escape the text so as to be used
    as a part of an HTML document.

    Taken from python Wiki.
    """
    html_escape_table = {'"': "&quot;", "'": "&apos;"}
    return escape(text, html_escape_table)
