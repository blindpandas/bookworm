# coding: utf-8

from __future__ import annotations
import sys
import os
import multiprocessing as mp
from traceback import format_exception
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, partial
from dataclasses import dataclass, field
import bookworm.typehints as t
from bookworm.signals import app_shuttingdown
from bookworm.logger import logger


log = logger.getChild(__name__)


# An executor for background tasks (designated for i/o bound tasks)
threaded_worker = ThreadPoolExecutor(thread_name_prefix="bookworm_threaded_worker")

# An executor for background tasks (designated for CPU bound tasks)
process_worker = ProcessPoolExecutor()


@app_shuttingdown.connect
def _shutdown_threaded_worker(sender):
    """Cancel any pending background tasks."""
    log.debug("Canceling  background tasks.")
    threaded_worker.shutdown(wait=False)
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
            log.debug(
                f"Failed to submit function {func}; the thread executor is shutting down."
            )

    return wrapper


@dataclass(repr=False)
class CancellationToken:
    _cancel_event: mp.Event = field(default_factory=mp.Event)

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


@dataclass
class QPChannel:
    queue: mp.Queue = field(default_factory=mp.Queue)
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)

    def cancel(self):
        self.queue.put((QPResult.CANCELLED, None))

    def __post_init__(self):
        self.is_cancellation_requested = (
            self.cancellation_token.is_cancellation_requested
        )

    def get(self):
        return self.queue.get()

    def push(self, value: t.Any):
        self.queue.put((QPResult.OK, value))

    def exception(self, exc_type, exc_value, tb):
        tb_text = "".join(format_exception(exc_type, exc_value, tb))
        self.queue.put((QPResult.FAILED, (exc_value, tb_text)))

    def log(self, msg: str):
        self.queue.put((QPResult.DEBUG, f"PID: {os.getpid()}; {msg}"))

    def done(self):
        self.queue.put((QPResult.COMPLETED, None))

    def close(self):
        self.queue.close()


class QueueProcess(mp.Process):
    """
    A process that passes a channel to its target.
    The process could be iterated over to get the produced
    results as they are generated.
    The target should recieve a keyword argument `channel`
    and use it to send results to the caller.
    """

    QPIteratorType = t.Iterator[t.Any]

    def __init__(self, *args, cancellable=True, **kwargs):
        kwargs.setdefault("daemon", True)
        super().__init__(*args, **kwargs)
        self.cancellable = cancellable
        self.channel = QPChannel()
        self._is_cancelled = mp.Event()
        self._done_callback = None

    def cancel(self):
        if not self.cancellable:
            raise TypeError("Uncancellable operation")
        self.channel.cancellation_token.request_cancellation()

    def is_cancelled(self):
        return self._is_cancelled.is_set()

    def add_done_callback(self, callback, *args, **kwargs):
        self._done_callback = partial(callback, *args, **kwargs)

    def run(self):
        try:
            self._target(*self._args, **self._kwargs, channel=self.channel)
        except:
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
            elif flag is QPResult.CANCELLED:
                self._is_cancelled.set()
                break
            elif flag is QPResult.FAILED:
                exc_value, tb_text = result
                log.exception(f"Remote exception from {self}.\nTraceback:\n{tb_text}")
                raise exc_value
        self.join()
        self.close()
