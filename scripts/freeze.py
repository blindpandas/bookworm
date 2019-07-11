# coding: utf-8

import py2exe
from glob import glob
from pathlib import Path
from setuptools import setup, find_packages
from bookworm import app


CWD = Path(__file__).parent
LONG_DESCRIPTION = (CWD / "README.md").read_text()

with open(CWD / "requirements.txt", "r") as reqs:
    REQUIREMENTS = [l.strip() for l in reqs.readlines()]


def get_data_files():
    from accessible_output2 import find_datafiles
    rv = find_datafiles()
    res = CWD / "bookworm" / "resources"
    to_str = lambda it: [str(i) for i in it]
    waves = to_str(res.rglob("*.wav"))
    txts = to_str(res.rglob("*.txt"))
    return rv + [("resources", waves + txts),]


setup(
    name=app.name,
    version=app.version,
    author=app.author,
    author_email=app.author_email,
    description="An accessible ebook reader.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/mush42/bookworm/",
    license="MIT",
    packages=find_packages(exclude=["tests"]),
    platforms="any",
    include_package_data=True,
    #package_data={"bookworm": ["resources/*"]},
    zip_safe=False,
    entry_points={"gui_scripts": ["bookworm=bookworm.__main__:main"]},
    install_requires=REQUIREMENTS,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Desktop Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
    ],
    windows=[
        {
            "script":"bookworm/__main__.py",
            "dest_base":"Bookworm",
            "icon_resources":[(1, "resources/bookworm.ico")],
            "version": "1.0.0",
            "description":"Bookworm, the accessible ebook reader",
            "product_version": "1.0.0",
            "copyright": "Musharraf Omer",
            "company_name": "MushyTech",
        },
    ],
    options = {"py2exe": {
        "bundle_files": 3,
        "excludes": [
            "Tkinter",
            "serial.loopback_connection",
            "serial.rfc2217",
            "serial.serialcli",
            "serial.serialjava",
            "serial.serialposix",
            "serial.socket_connection"
        ],
        "packages": find_packages(),
        "includes": [],
    }},
    data_files=get_data_files()
)
