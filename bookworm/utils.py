# coding: utf-8

import wx
import hashlib
from functools import wraps
from pathlib import Path
from xml.sax.saxutils import escape
from bookworm.concurrency import call_threaded
from bookworm.logger import logger


log = logger.getChild(__name__)


# Sentinel
_missing = object()


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


def _gen_sha1hash(filename):
    hasher = hashlib.sha1()
    with open(filename, "rb") as file:
        for chunk in file:
            hasher.update(chunk)
    return hasher.hexdigest()


@call_threaded
def generate_sha1hash(filename):
    return _gen_sha1hash(filename)


def search(pattern, text):
    """Search the given text using a compiled regular expression."""
    mat = pattern.search(text, concurrent=True)
    if not mat:
        return
    pos = mat.span()[0]
    lseg, tseg, rseg = pattern.split(text, maxsplit=1)
    snipit = "".join([lseg[-20:], tseg, rseg[:20]])
    return (pos, snipit)


class cached_property(property):

    """A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::

        class Foo(object):

            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a `__dict__` in order for this property to
    work.
    
    Taken as is from werkzeug, a WSGI toolkit for python.
    :copyright: (c) 2014 by the Werkzeug Team.
    """

    # implementation detail: A subclass of python's builtin property
    # decorator, we override __get__ to check for a cached value. If one
    # choses to invoke __get__ by hand the property will still work as
    # expected because the lookup logic is replicated in __get__ for
    # manual invocation.

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


def escape_html(text):
    """Escape the text so as to be used
    as a part of an HTML document.
    
    Taken from python Wiki.
    """
    html_escape_table = {'"': "&quot;", "'": "&apos;"}
    return escape(text, html_escape_table)
