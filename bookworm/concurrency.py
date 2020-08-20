# coding: utf-8

import sys
import os
import multiprocessing as mp
from traceback import format_exception
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps
from dataclasses import dataclass
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


class QPResult(IntEnum):
    COMPLETED = -1
    OK = 0
    FAILED = 1
    DEBUG = 2


@dataclass
class QPChannel:
    queue: mp.Queue

    def push(self, value: t.Any):
        self.queue.put((QPResult.OK, value))

    def exception(self, exc_type, exc_value, tb):
        tb_text = "".join(format_exception(exc_type, exc_value, tb))
        self.queue.put((QPResult.FAILED, (exc_value, tb_text)))

    def log(self, msg: str):
        self.queue.put((QPResult.DEBUG, f"PID: {os.getpid()}; {msg}"))

    def close(self):
        self.queue.put((QPResult.COMPLETED, None))
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

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("daemon", True)
        super().__init__(*args, **kwargs)
        self.queue = mp.Queue()

    def run(self):
        channel = QPChannel(self.queue)
        try:
            self._target(*self._args, **self._kwargs, channel=channel)
        except:
            channel.exception(*sys.exc_info())

    def close(self):
        super().close()
        self.queue.close()

    def __iter__(self) -> QPIteratorType:
        return self.iter_queue()

    def iter_queue(self) -> QPIteratorType:
        if self.is_alive():
            raise RuntimeError("Can only iterate process once.")
        self.start()
        while True:
            flag, result = self.queue.get()
            if flag is QPResult.OK:
                yield result
            elif flag is QPResult.DEBUG:
                log.debug(f"REMOTE PROCESS: {result}")
            elif flag is QPResult.COMPLETED:
                break
            elif flag is QPResult.FAILED:
                exc_value, tb_text = result
                log.exception(f"Remote exception from {self}.\nTraceback:\n{tb_text}")
                raise exc_value
        self.join()
        self.close()
