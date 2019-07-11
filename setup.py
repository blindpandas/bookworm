from pathlib import Path
from setuptools import setup, find_packages
from bookworm import app


CWD = Path(__file__).parent
LONG_DESCRIPTION = (CWD / "README.md").read_text()

with open(CWD / "requirements.txt", "r") as reqs:
    REQUIREMENTS = [l.strip() for l in reqs.readlines()]


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
    platforms=["Windows"],
    include_package_data=True,
    zip_safe=False,
    entry_points={"gui_scripts": ["bookworm=bookworm.__main__:main"]},
    install_requires=REQUIREMENTS,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Desktop Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System ::Windows",
        "Programming Language :: Python :: 3.7",
    ],
)
