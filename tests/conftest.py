import pytest
from pathlib import Path


HERE = Path(__file__).parent


@pytest.fixture()
def ebooks_dir():
    """Return the path for the directory that contains ebook files used in tests."""
    return HERE / ".ebooks"
