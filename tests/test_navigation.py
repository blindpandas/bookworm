from types import SimpleNamespace

import pytest

from bookworm.gui import book_viewer
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.structured_text import SemanticElementType
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser


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


def test_empty_href_does_not_reassign_previous_link_target():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <p>
                <a href="https://one.example">one</a>
                <a href="#empty"></a>
                <span id="empty">target</span>
            </p>
        </body></html>
        """
    )
    text = parser.get_text()
    link_range = next(iter(parser.link_targets))

    assert text[link_range[0] : link_range[1]] == "one"
    assert parser.link_targets[link_range] == "https://one.example"


def test_named_anchor_without_href_is_not_a_semantic_link():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <p><a name="spot">anchor text</a> <a href="#spot">jump</a></p>
        </body></html>
        """
    )
    text = parser.get_text()

    link_texts = [
        text[start:stop] for start, stop in parser.semantic_elements[SemanticElementType.LINK]
    ]

    assert link_texts == ["jump"]


def test_table_links_without_reliable_targets_are_not_semantic_links():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <table>
                <tr>
                    <td><a href="https://example.com/table">table link</a></td>
                </tr>
            </table>
        </body></html>
        """
    )

    assert parser.link_targets == {}
    assert SemanticElementType.LINK not in parser.semantic_elements
    assert len(parser.semantic_elements[SemanticElementType.TABLE]) == 1


def test_table_links_do_not_misalign_with_non_rendered_links():
    parser = StructuredHtmlParser.from_string(
        """
        <html><body>
            <table>
                <tr>
                    <td>
                        <a href="https://example.com/hidden">
                            <span style="display:none">hidden</span>
                        </a>
                        <a href="https://example.com/visible">visible link</a>
                    </td>
                </tr>
            </table>
        </body></html>
        """
    )

    assert parser.link_targets == {}
    assert SemanticElementType.LINK not in parser.semantic_elements
