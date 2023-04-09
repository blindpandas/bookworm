# coding: utf-8

from pathlib import Path

from setuptools import find_packages, setup

from bookworm import app

# Invalid requirement specifier prefixes
INVALID_PREFIXES = (
    "http://",
    "https://",
    "git+",
)


CWD = Path(__file__).parent
LONG_DESCRIPTION = "Bookworm is the universally accessible document reader.\nVisit [the project's home](https://github.com/blindpandas/bookworm) for more information."

REQUIREMENTS = []
with open(CWD / "requirements-app.txt", "r") as reqs:
    for line in reqs:
        if any(line.startswith(prfx) for prfx in INVALID_PREFIXES):
            continue
        REQUIREMENTS.append(line)

setup(
    name=app.name,
    version=app.version,
    author=app.author,
    author_email=app.author_email,
    description="The universally accessible document reader",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/mush42/bookworm/",
    download_url=app.website,
    license="GPL v2.0",
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
        "document",
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
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
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
