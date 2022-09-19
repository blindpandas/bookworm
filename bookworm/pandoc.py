# coding: utf-8

from __future__ import annotations

import functools
import os
import platform
import shutil
import subprocess

from bookworm import app
from bookworm.paths import data_path
from bookworm.platforms import PLATFORM

DEFAULT_PANDOC_ARGS = (
    "-s",
    "+RTS",
    "-M112m",
    "-RTS",
)


def is_pandoc_supported():
    return all([PLATFORM == "win32", platform.machine() == "AMD64"])


def get_pandoc_path():
    return data_path("pandoc")


def is_pandoc_installed():
    return is_pandoc_supported() and shutil.which(
        "pandoc", path=os.fspath(get_pandoc_path())
    )


@functools.cache
def get_pandoc_executable():
    return get_pandoc_path().joinpath("pandoc.exe")


def call_pandoc(args, popen_kwargs=None):
    popen_kwargs = popen_kwargs or {}
    args = [os.fspath(get_pandoc_executable()), *args]
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    ret = subprocess.run(
        args,
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        startupinfo=startupinfo,
        **popen_kwargs,
    )
    ret.check_returncode()
    return ret.stdout


def convert(from_format, to_format, input_file=None, output_file=None, input_data=None):
    kwargs = {"timeout": 300}
    args = [
        *DEFAULT_PANDOC_ARGS,
        "-f",
        from_format,
        "-t",
        to_format,
    ]
    if output_file is not None:
        args.extend(["-o", os.fspath(output_file)])
    if input_file is not None:
        args.append(os.fspath(input_file))
    elif input_data is not None:
        kwargs["input"] = input_data
    else:
        raise TypeError("Pandoc: No input file was passed and no input_data provided.")
    ret = call_pandoc(args, kwargs)
    if output_file is None:
        return ret
    return True


def get_version():
    return (
        call_pandoc(["--version"]).decode("utf-8").split("\n")[0].split(" ")[-1].strip()
    )
