# coding: utf-8

import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps
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


def call_threaded(func):
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


class QueueProcess(mp.Process):
    """A `Process` that passes a queue to
    its target function.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("daemon", True)
        super().__init__(*args, **kwargs)
        self.queue = mp.Queue()

    def run(self):
        self._target(*self._args, **self._kwargs, queue=self.queue)

    def close(self):
        super().close()
        self.queue.close()
