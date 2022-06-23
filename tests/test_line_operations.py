import pytest

from bookworm.utils import remove_excess_blank_lines


def test_remove_excess_blank_lines_without_effecting_structure():
    raw_text = (
        "Hello\n\r\n\n\n"
        "world\n    \n\r\n"
        "For me"
        "with this\r\r"
    )
    processed_text = remove_excess_blank_lines(raw_text)
    assert '\r' not in processed_text
    assert '\n\n' not in processed_text
    assert len(processed_text) == len(raw_text)
    raw_lines = [line for line in raw_text.split("\n") if line.strip()]
    processed_lines = [line for line in raw_text.split("\n") if line.strip()]
    assert len(processed_lines) == len(raw_lines)
    for (rl, pl) in zip(raw_lines, processed_lines):
        assert rl[:3] == pl[:3]
