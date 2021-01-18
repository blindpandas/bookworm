#!/usr/bin/env python

from pathlib import Path
from setuptools import setup, find_packages
from bookworm import app


CWD = Path(__file__).parent
LONG_DESCRIPTION = (CWD / "README.md").read_text()

with open(CWD / "requirements.txt", "r") as reqs:
    REQUIREMENTS = [l.strip() for l in reqs.readlines() if not l.startswith("git")]


setup(
    name=app.name,
    version=app.version,
    author=app.author,
    author_email=app.author_email,
    description="The universally accessible ebook reader",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/mush42/bookworm/",
    download_url=app.website,
    license="MIT",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "gui_scripts": ["bookworm=bookworm.__main__:main"],
    },
    install_requires=REQUIREMENTS,
    platforms=["Windows", "Linux"],
    keywords=[
        "reader",
        "eBook",
        "accessibility",
        "a11y",
        "blind",
        "pdf",
        "epub",
        "tts",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Desktop Environment",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows :: Windows 7",
        "Operating System :: Microsoft :: Windows :: Windows 8",
        "Operating System :: Microsoft :: Windows :: Windows 8.1",
        "Operating System :: Microsoft :: Windows :: Windows 10 ",
        "Operating System :: POSIX :: Linux ",
        "Programming Language :: Python :: 3.7",
        "Topic :: Adaptive Technologies",
        "Topic :: Desktop Environment :: Gnome",
        "Topic :: Education",
    ],
)
