import sys
from types import SimpleNamespace

import pytest

if sys.platform != "win32":
    pytest.skip("Windows OCR requires Windows", allow_module_level=True)

from bookworm.platforms.win32 import docr_engine


def test_ocr_result_preserves_line_breaks():
    result = SimpleNamespace(
        lines=[SimpleNamespace(text="First line"), SimpleNamespace(text="Second line")]
    )

    assert docr_engine._get_recognized_text(result) == "First line\nSecond line\n"
    assert docr_engine._get_recognized_text(SimpleNamespace(lines=[])) == ""
