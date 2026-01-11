
import sys
from pathlib import Path

# Ensure local package is importable
sys.path.append(str(Path(__file__).parent))

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


setup(
    name=app.name,
    version=app.version,
    author=app.author,
    author_email=app.author_email,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    platforms=["Windows", "Linux"],
)
