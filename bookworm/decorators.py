from functools import wraps


def only_when_reader_ready(f):
    """Execute this function only if the reader is ready."""
    @wraps(f)
    def wrapper(self, *a, **kw):
        if not self.reader.ready:
            return
        return f(self, *a, **kw)
    return wrapper



def only_if_pagination_is_supported(f):
    """Execute this function only if the reader supports pagination."""
    @wraps(f)
    def wrapper(self, *a, **kw):
        if not self.reader.supports_pagination:
            return
        return f(self, *a, **kw)
    return wrapper

