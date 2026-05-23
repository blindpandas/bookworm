from types import SimpleNamespace

import pytest

from bookworm.gui import book_viewer
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.structured_text import SemanticElementType


class StructuralNavigationHarness:
    navigate_to_structural_element = BookViewerWindow.navigate_to_structural_element


def line_bounds(text, pos):
    pos = max(0, min(pos, len(text)))
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    if end == -1:
        end = len(text)
    return start, end


def noop(*_args, **_kwargs):
    pass


@pytest.mark.parametrize(
    "element_type",
    [
        SemanticElementType.LIST,
        SemanticElementType.TABLE,
        SemanticElementType.QUOTE,
    ],
)
def test_structural_navigation_moves_multiline_elements_to_first_line(monkeypatch, element_type):
    text = "intro\nfirst element line\nsecond element line\noutro\n"
    start = text.index("first element line")
    stop = text.index("\noutro")
    viewer = StructuralNavigationHarness()
    viewer._BookViewerWindow__latest_structured_navigation_position = None
    viewer.insertion_point = 0

    def get_semantic_element(_requested_type, _forward, _anchor):
        return (start, stop), element_type

    viewer.reader = SimpleNamespace(
        ready=True,
        get_semantic_element=get_semantic_element,
    )
    viewer.get_insertion_point = lambda: viewer.insertion_point
    viewer.get_containing_line = lambda pos: line_bounds(text, pos)
    viewer.get_text_by_range = lambda range_start, range_stop: text[range_start:range_stop]
    viewer.set_insertion_point = lambda pos: setattr(viewer, "insertion_point", pos)

    monkeypatch.setattr(book_viewer.speech, "announce", noop)
    monkeypatch.setattr(
        book_viewer.sounds,
        "structured_navigation",
        SimpleNamespace(play=noop),
    )
    monkeypatch.setattr(
        book_viewer.reading_position_change,
        "send",
        noop,
    )

    BookViewerWindow.navigate_to_structural_element(viewer, element_type, True)

    assert viewer.insertion_point == start
