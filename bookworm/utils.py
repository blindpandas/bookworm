# coding: utf-8

import sys
import regex
import wx
import hashlib
from functools import wraps
from pathlib import Path
from xml.sax.saxutils import escape
from bookworm import typehints as t
from bookworm import app
from bookworm.concurrency import call_threaded
from bookworm.platform_services.runtime import system_start_app
from bookworm.logger import logger


log = logger.getChild(__name__)


# Sentinel
_missing = object()

# New line character
UNIX_NEWLINE = '\n'
WINDOWS_NEWLINE = '\r\n'
MAC_NEWLINE = '\r'
NEWLINE = UNIX_NEWLINE
MORE_THAN_ONE_LINE = regex.compile(r"[\n]{2,}")


def normalize_line_breaks(text, line_break=UNIX_NEWLINE):
    text = text.replace(WINDOWS_NEWLINE, UNIX_NEWLINE).replace(MAC_NEWLINE, UNIX_NEWLINE)
    if line_break != UNIX_NEWLINE:
        text = text.replace(UNIX_NEWLINE, line_break)
    return text


def remove_excess_blank_lines(text):
    return MORE_THAN_ONE_LINE.sub("\n", normalize_line_breaks(text))


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


@call_threaded
def generate_sha1hash_async(filename):
    return generate_sha1hash(filename)


def search(pattern, text):
    """Search the given text using a compiled regular expression."""
    snip_reach = 25
    len_text = len(text)
    for mat in pattern.finditer(text, concurrent=True):
        start, end = mat.span()
        snip_start = 0 if start <= snip_reach else (start - snip_reach)
        snip_end = len_text if (end + snip_reach) >= len_text else (end + snip_reach)
        snip = text[snip_start:snip_end].split()
        if len(snip) > 3:
            snip.pop(0)
            snip.pop(-1)
        yield (start, " ".join(snip))


def format_datetime(date) -> str:
    return app.current_language.format_datetime(date)


def escape_html(text):
    """Escape the text so as to be used
    as a part of an HTML document.

    Taken from python Wiki.
    """
    html_escape_table = {'"': "&quot;", "'": "&apos;"}
    return escape(text, html_escape_table)
