from pathlib import Path

import pytest


@pytest.fixture(scope="function", autouse=True)
def asset():
    yield lambda filename: str(Path(__file__).parent / "assets" / filename)
