# coding: utf-8

from __future__ import annotations
import sys
import os
import time
import atexit
import socket
import errno
import contextlib
import waitress
from multiprocessing.shared_memory import SharedMemory
from bottle import Bottle
from bookworm.signals import local_server_booting
from bookworm.commandline_handler import (
    BaseSubcommandHandler,
    register_subcommand,
    run_subcommand_in_a_new_process,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


BOOKWORM_LOCAL_SERVER_DEFAULT_PORT = 61073
BOOKWORM_LOCAL_SERVER_SHARED_MEMORY_NAME = "bkw.local.server.port"
BOOKWORM_LOCAL_SERVER_SHARED_MEMORY_SIZE = 4
SERVER_READY_TIMEOUT = 120


def get_local_server_netloc():
    server_port = LocalServerSubcommand.get_local_server_port()
    if server_port is not None:
        return f"http://localhost:{server_port}"
    run_subcommand_in_a_new_process(args=[LocalServerSubcommand.subcommand_name,])
    now = time.monotonic()
    while (time.monotonic() - now) <= SERVER_READY_TIMEOUT:
        server_port = LocalServerSubcommand.get_local_server_port()
        if server_port is not None:
            return f"http://localhost:{server_port}"
        else:
            time.sleep(1)
    raise TimeoutError("Server timed out. Failed to start the server.")


@register_subcommand
class LocalServerSubcommand(BaseSubcommandHandler):
    subcommand_name = "local_server"

    @classmethod
    def add_arguments(cls, subparser):
        pass

    @classmethod
    def handle_commandline_args(cls, args):
        if (server_port := cls.get_local_server_port()) is not None:
            log.info(f"Local server is already running at port {server_port}")
        else:
            log.info("Server is not running.")
            cls.run_server()
        return 0

    @classmethod
    def run_server(cls):
        log.debug("Starting local server...")
        server_port = (
            BOOKWORM_LOCAL_SERVER_DEFAULT_PORT
            if cls.is_free_port(BOOKWORM_LOCAL_SERVER_DEFAULT_PORT)
            else cls.find_free_port()
        )
        log.debug(f"Choosing port {server_port} to run at...")
        shm = SharedMemory(
            BOOKWORM_LOCAL_SERVER_SHARED_MEMORY_NAME,
            create=True,
            size=BOOKWORM_LOCAL_SERVER_SHARED_MEMORY_SIZE,
        )
        shm.buf[:BOOKWORM_LOCAL_SERVER_SHARED_MEMORY_SIZE] = server_port.to_bytes(
            BOOKWORM_LOCAL_SERVER_SHARED_MEMORY_SIZE, sys.byteorder
        )
        atexit.register(shm.unlink)
        app = Bottle()
        local_server_booting.send(app)
        log.debug(f"Local server is running at: localhost:{server_port}")
        waitress.serve(app, listen=f"localhost:{server_port}")
        shm.unlink()

    @staticmethod
    def get_local_server_port():
        try:
            shm = SharedMemory(BOOKWORM_LOCAL_SERVER_SHARED_MEMORY_NAME, create=False)
        except FileNotFoundError:
            return
        else:
            retval = int.from_bytes(bytes(shm.buf), sys.byteorder)
            shm.close()
            return retval

    @staticmethod
    def is_free_port(port):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            try:
                s.bind(("localhost", port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return True
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    return False
                else:
                    raise

    @staticmethod
    def find_free_port():
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("localhost", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]
