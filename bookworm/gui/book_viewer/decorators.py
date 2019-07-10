# coding: utf-8

import wx
from functools import wraps


def only_when_reader_ready(f):
    """Execute this function only if the reader is ready."""
    # XXX We don't need this any more, remove it gradually!
    @wraps(f)
    def wrapper(self, *a, **kw):
        if not self.reader.ready:
            arg = None if not a else a[0]
            if arg and isinstance(arg, wx.Event):
                arg.Skip()
            return
        return f(self, *a, **kw)

    return wrapper
