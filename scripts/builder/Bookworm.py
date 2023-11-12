# coding: utf-8

import os
import sys

# sys.stdout = open(os.devnull, "w+")
# sys.stderr = open(os.devnull, "w+")

import multiprocessing

multiprocessing.freeze_support()


def suppress_console_window() -> None:
    """We need to be able to use CLI args even when bookworm is an executable
    The issue is that when compiling in windowed mode, we have no access to stdin, stdout and stderr, because of how windows, and python behave in these circumstances
    Specifically, in windowed mode, pythonw.exe is used, rather than python.exe
    This hack hides the console window when bookworm starts, obtaining the same effect of windowed mode, but retaining the option to use CLI arguments
    Code taken from: https://stackoverflow.com/questions/67610859/show-stdout-with-pyinstaller-noconsole
    """
    import ctypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    process_array = (ctypes.c_uint8 * 1)()
    num_processes = kernel32.GetConsoleProcessList(process_array, 1)
    if num_processes < 3:
        ctypes.WinDLL('user32').ShowWindow(kernel32.GetConsoleWindow(), 0)


if __name__ == "__main__":
    from bookworm import bookworm

    suppress_console_window()
    bookworm.main()
