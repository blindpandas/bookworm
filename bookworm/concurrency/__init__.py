# coding: utf-8

from __future__ import annotations
import sys
import os
import threading
import multiprocessing as mp
import inspect
import attr
from traceback import format_exception
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, partial
from contextlib import suppress
import bookworm.typehints as t
from bookworm.signals import app_starting, app_shuttingdown
from bookworm.logger import logger


log = logger.getChild(__name__)


# An executor for background tasks (designated for i/o bound tasks)
threaded_worker = ThreadPoolExecutor(thread_name_prefix="bookworm_threaded_worker")

# An executor for background tasks (designated for CPU bound tasks)
process_worker = ProcessPoolExecutor()


@app_shuttingdown.connect
def _shutdown_concurrent_workers(sender):
    """Cancel any pending background tasks."""
    log.debug("Canceling  background tasks.")
    threaded_worker.shutdown(wait=False, cancel_futures=True)
    process_worker.shutdown(wait=False)


def call_threaded(func: t.Callable[..., None]) -> t.Callable[..., "Future"]:
    """Call `func` in a separate thread. It wraps the function
    in another function that returns a `concurrent.futures.Future`
    object when called.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return threaded_worker.submit(func, *args, **kwargs)
        except RuntimeError:
            log.debug(f"Failed to submit function {func}.")

    return wrapper


class OperationCancelled(Exception):
    """Raised in the generator to cancel the operation."""


@attr.s(auto_attribs=True, slots=True, getstate_setstate=True, repr=False)
class CancellationToken:
    _cancel_event: mp.Event = attr.ib(factory=mp.Event)

    def request_cancellation(self):
        self._cancel_event.set()

    def is_cancellation_requested(self):
        return self._cancel_event.is_set()


class QPResult(IntEnum):
    CANCELLED = -2
    COMPLETED = -1
    OK = 0
    FAILED = 1
    DEBUG = 2


class QPChannel:
    def __init__(self):
        self.reader, self.writer = mp.Pipe(duplex=False)
        self.cancellation_token = CancellationToken()
        self.is_cancellation_requested = (
            self.cancellation_token.is_cancellation_requested
        )

    def get(self):
        return self.reader.recv()

    def cancel(self):
        self.writer.send((QPResult.CANCELLED, None))

    def push(self, value: t.Any):
        self.writer.send((QPResult.OK, value))

    def exception(self, exc_type, exc_value, tb):
        tb_text = "".join(format_exception(exc_type, exc_value, tb))
        self.writer.send((QPResult.FAILED, (exc_value, tb_text)))

    def log(self, msg: str):
        self.writer.send((QPResult.DEBUG, f"PID: {os.getpid()}; {msg}"))

    def done(self):
        self.writer.send((QPResult.COMPLETED, None))

    def close(self):
        self.reader.close()
        self.writer.close()


class QueueProcess(mp.Process):
    """
    A process that runs a generator in parallel, yielding values from it.
    You can iterate the process object to get the values.
    Note that iteration is blocking.
    You can also use the map method for asynchronous iteration.
    """

    QPIteratorType = t.Iterator[t.Any]

    def __init__(self, *args, cancellable=True, **kwargs):
        kwargs.setdefault("daemon", True)
        super().__init__(*args, **kwargs)
        assert inspect.isgeneratorfunction(
            self._target
        ), "QueueProcess target should be a generator function."
        self.cancellable = cancellable
        self.channel = QPChannel()
        self._done_callback = None

    def cancel(self):
        if not self.cancellable:
            raise TypeError("Uncancellable operation")
        self.channel.cancellation_token.request_cancellation()

    def is_cancelled(self):
        return self.channel.cancellation_token.is_cancellation_requested()

    def add_done_callback(self, callback, *args, **kwargs):
        self._done_callback = partial(callback, *args, **kwargs)

    def _generator(self):
        _producer = self._target(*self._args, **self._kwargs)
        try:
            for item in _producer:
                yield item
        except GeneratorExit:
            _producer.close()
            self.channel.cancel()

    def run(self):
        gen = self._generator()
        try:
            while True:
                item = next(gen)
                self.channel.push(item)
                if self.is_cancelled():
                    gen.close()
        except StopIteration:
            self.channel.done()
        except Exception as e:
            self.channel.exception(*sys.exc_info())

    def close(self):
        self.channel.close()
        super().close()

    def __iter__(self) -> QPIteratorType:
        return self.iter_queue()

    def iter_queue(self) -> QPIteratorType:
        if self.is_alive():
            raise RuntimeError("Can only iterate process once.")
        self.start()
        try:
            while True:
                flag, result = self.channel.get()
                if flag is QPResult.OK:
                    yield result
                elif flag is QPResult.DEBUG:
                    log.debug(f"REMOTE PROCESS: {result}")
                elif flag is QPResult.COMPLETED:
                    if self._done_callback is not None:
                        self._done_callback()
                    break
                elif flag is QPResult.FAILED:
                    exc_value, tb_text = result
                    log.exception(
                        f"Remote exception from {self}.\nTraceback:\n{tb_text}"
                    )
                    raise exc_value
                elif flag is QPResult.CANCELLED:
                    break
        finally:
            self.join()
            self.close()

    @call_threaded
    def map(self, callback):
        """Asynchronously generate values and invoke the given callback with each generated value."""
        for value in self:
            callback(value)
