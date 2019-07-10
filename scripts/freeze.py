# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from pathlib import Path
import py2exe
import os
import app
from glob import glob


def get_data():
    return [("sounds", ["sounds/pagination.wav"])]


if __name__ == "__main__":
    setup(
        name=app.identifier,
        author=app.author,
        author_email=app.author_email,
        version=app.version,
        url=app.url,
        packages=find_packages(exclude=["tests"]),
        data_files=get_data(),
        options={
            "py2exe": {
                "optimize": 2,
                "packages": [],
                "dll_excludes": [],
                "compressed": True,
            }
        },
        windows=[{"script": "main.py", "dest_base": "bookworm"}],
        install_requires=[],
    )
