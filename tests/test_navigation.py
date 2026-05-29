from types import SimpleNamespace

import pytest

from bookworm.gui import book_viewer
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.gui.book_viewer.position_mapping import TextCtrlPositionMap
from bookworm.structured_text import SemanticElementType
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser


class StructuralNavigationHarness:
    navigate_to_structural_element = BookViewerWindow.navigate_to_structural_element


class PositionMappingHarness:
    control_to_view_position = BookViewerWindow.control_to_view_position
    view_to_control_position = BookViewerWindow.view_to_control_position
    get_insertion_point = BookViewerWindow.get_insertion_point
    get_containing_line = BookViewerWindow.get_containing_line
    get_line_number = BookViewerWindow.get_line_number


class SetContentHarness(PositionMappingHarness):
    set_content = BookViewerWindow.set_content
    set_insertion_point = BookViewerWindow.set_insertion_point

    def __init__(self, content_style):
        self._has_text_zoom = False
        self.content_style = content_style
        self.contentTextCtrl = StyleRecordingTextCtrl()

    def get_content_view_text_style(self, font_size=None):
        assert font_size is None
        return self.content_style


class StyleRecordingTextCtrl:
    def __init__(self):
        self.calls = []
        self.value = ""

    def Freeze(self):
        self.calls.append(("Freeze",))

    def Thaw(self):
        self.calls.append(("Thaw",))

    def SetDefaultStyle(self, style):
        self.calls.append(("SetDefaultStyle", style))

    def SetValue(self, value):
        self.value = value
        self.calls.append(("SetValue", value))

    def GetLastPosition(self):
        return len(self.value)

    def SetStyle(self, start, stop, style):
        self.calls.append(("SetStyle", start, stop, style))

    def ShowPosition(self, pos):
        self.calls.append(("ShowPosition", pos))

    def SetInsertionPoint(self, pos):
        self.calls.append(("SetInsertionPoint", pos))

    def SetFocusFromKbd(self):
        self.calls.append(("SetFocusFromKbd",))


class LineNumberTextCtrl:
    def __init__(self, insertion_point=0):
        self.insertion_point = insertion_point
        self.position_queries = []

    def GetInsertionPoint(self):
        return self.insertion_point

    def PositionToXY(self, pos):
        self.position_queries.append(pos)
        return 0, 0, pos


class ContainingLineTextCtrl:
    def __init__(self, line_start, line_end):
        self.line_start = line_start
        self.line_end = line_end
        self.position_queries = []

    def GetContainingLine(self, pos):
        self.position_queries.append(pos)
        return self.line_start, self.line_end


def line_bounds(text, pos):
    pos = max(0, min(pos, len(text)))
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    if end == -1:
        end = len(text)
    return start, end


def noop(*_args, **_kwargs):
    pass


def test_position_mapping_handles_non_bmp_rich_edit_offsets():
    text = "\U0001d445a\U0001d446\U0001d447bc"
    position_map = TextCtrlPositionMap(text)

    assert position_map.control_to_view_position(0) == -1
    assert position_map.view_to_control_position(-1) == 0

    expected_control_positions = [1, 3, 4, 6, 8, 9, 10]
    assert [
        position_map.view_to_control_position(position) for position in range(len(text) + 1)
    ] == expected_control_positions

    for view_position, control_position in enumerate(expected_control_positions):
        assert position_map.control_to_view_position(control_position) == view_position

    trailing_sentinel_position = position_map.view_to_control_position(len(text)) + 1
    assert position_map.control_to_view_position(trailing_sentinel_position) == len(text)
    assert position_map.to_text_ctrl_value() == f"\n{text}\n\n\n\n"


def test_line_lookup_maps_non_bmp_text_positions_to_native_control_positions():
    text = "exercise with \U0001d445\U0001d446\U0001d447 before heading\nHeading\nbody"
    heading_start = text.index("Heading")
    non_bmp_before_heading = 3
    control_heading_start = 1 + heading_start + non_bmp_before_heading
    viewer = PositionMappingHarness()
    viewer._text_position_map = TextCtrlPositionMap(text)
    viewer.contentTextCtrl = ContainingLineTextCtrl(
        control_heading_start,
        control_heading_start + len("Heading"),
    )

    assert viewer.get_containing_line(heading_start) == (
        heading_start,
        heading_start + len("Heading"),
    )
    assert viewer.contentTextCtrl.position_queries == [control_heading_start]


def test_get_line_number_uses_raw_caret_when_position_is_omitted():
    viewer = PositionMappingHarness()
    viewer._text_position_map = TextCtrlPositionMap("first line")
    viewer.contentTextCtrl = LineNumberTextCtrl(insertion_point=0)

    assert viewer.get_line_number() == 0
    assert viewer.contentTextCtrl.position_queries == [0]


def test_set_content_reapplies_text_style_after_setting_control_value():
    text = "intro \U0001d445\U0001d446"
    content_style = object()
    viewer = SetContentHarness(content_style)

    viewer.set_content(text)

    text_ctrl_value = TextCtrlPositionMap(text).to_text_ctrl_value()
    assert viewer.contentTextCtrl.value == text_ctrl_value
    assert viewer.contentTextCtrl.calls[1:4] == [
        ("SetValue", text_ctrl_value),
        ("SetStyle", 0, len(text_ctrl_value), content_style),
        ("SetDefaultStyle", content_style),
    ]


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
