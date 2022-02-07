# coding: utf-8

from __future__ import annotations
import threading
import asyncio
from functools import wraps
import bookworm.typehints as t
from bookworm.signals import app_starting, app_shuttingdown
from bookworm.logger import logger


log = logger.getChild(__name__)


# Asyncio event loop
ASYNCIO_EVENT_LOOP = asyncio.new_event_loop()
ASYNCIO_LOOP_THREAD = None


@app_shuttingdown.connect
def _shutdown_asyncio_event_loop(sender):
    if ASYNCIO_LOOP_THREAD is not None:
        log.debug("Shutting down asyncio event loop")
        ASYNCIO_EVENT_LOOP.call_soon_threadsafe(ASYNCIO_EVENT_LOOP.stop)


def start_asyncio_event_loop():
    """Start an ambient event loop in another thread to carry out I/O."""

    global ASYNCIO_LOOP_THREAD
    if ASYNCIO_LOOP_THREAD is not None:
        log.debug(
            "Attempted to start the asyncio eventloop while it is already running"
        )
        return

    def _thread_target():
        global ASYNCIO_EVENT_LOOP
        log.info("Starting asyncio event loop")
        asyncio.set_event_loop(ASYNCIO_EVENT_LOOP)
        ASYNCIO_EVENT_LOOP.run_forever()

    ASYNCIO_LOOP_THREAD = threading.Thread(
        target=_thread_target, daemon=True, name="bookworm.asyncio.thread"
    )
    ASYNCIO_LOOP_THREAD.start()


def asyncio_coroutine_to_concurrent_future(func):
    """Returns a concurrent.futures.Future that wrapps the decorated async function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run_coroutine_threadsafe(
            func(*args, **kwargs), ASYNCIO_EVENT_LOOP
        )

    return wrapper


