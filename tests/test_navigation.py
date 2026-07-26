import sys
from types import SimpleNamespace

import pytest

from bookworm.document import SINGLE_PAGE_DOCUMENT_PAGER, Section
from bookworm.gui import book_viewer
from bookworm.gui.book_viewer import BookViewerWindow
from bookworm.gui.book_viewer.position_mapping import TextCtrlPositionMap
from bookworm.gui.contentview_ctrl import ContentViewCtrl
from bookworm.gui.text_ctrl_mixin import ContentViewCtrlMixin
from bookworm.structured_text import SemanticElementType, TextRange
from bookworm.structured_text.structured_html_parser import StructuredHtmlParser

if sys.platform == "win32":
    from bookworm.platforms.win32.controls import richedit


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
    set_content_view_font = BookViewerWindow.set_content_view_font
    set_insertion_point = BookViewerWindow.set_insertion_point

    def __init__(self, content_style):
        self._has_text_zoom = False
        self.content_style = content_style
        self.contentTextCtrl = StyleRecordingTextCtrl()

    def get_content_view_text_style(self, font_size=None):
        assert font_size is None
        return self.content_style


class TocFocusHarness:
    def __init__(self, insertion_point, reader):
        self.insertion_point = insertion_point
        self.reader = reader
        self.selected_sections = []

    def get_insertion_point(self):
        return self.insertion_point

    def tocTreeSetSelection(self, section):  # noqa: N802
        self.selected_sections.append(section)


class StyleRecordingTextCtrl:
    def __init__(self):
        self.calls = []
        self.value = ""
        self.default_font_result = True

    def Freeze(self):
        self.calls.append(("Freeze",))

    def Thaw(self):
        self.calls.append(("Thaw",))

    def SetDefaultStyle(self, style):
        self.calls.append(("SetDefaultStyle", style))

    def set_all_text_font(self, font):
        self.calls.append(("set_all_text_font", font))
        return True

    def set_default_text_font(self, font):
        self.calls.append(("set_default_text_font", font))
        return self.default_font_result

    def set_all_text_point_size(self, point_size):
        self.calls.append(("set_all_text_point_size", point_size))
        return True

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


class FakeFocusEvent:
    def __init__(self):
        self.skipped = False
        self.focused = False

    def Skip(self, skip=True):  # noqa: N802
        self.skipped = skip

    def GetEventObject(self):  # noqa: N802
        return self

    def SetFocus(self):  # noqa: N802
        self.focused = True


def line_bounds(text, pos):
    pos = max(0, min(pos, len(text)))
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    if end == -1:
        end = len(text)
    return start, end


def noop(*_args, **_kwargs):
    pass


def make_section(title, start, stop):
    return Section(
        title=title,
        pager=SINGLE_PAGE_DOCUMENT_PAGER,
        text_range=TextRange(start, stop),
    )


def test_toc_focus_syncs_tree_without_moving_single_page_reading_position():
    old_section = make_section("Old", 0, 10)
    current_section = make_section("Current", 40, 80)
    insertion_point = 50

    class FakeReader:
        ready = True
        active_section = old_section

        def __init__(self):
            self.set_active_section_calls = []
            self.document = SimpleNamespace(
                is_single_page_document=lambda: True,
                get_section_at_position=lambda _position: current_section,
            )

        def set_active_section(self, section, update_view=True):
            self.set_active_section_calls.append((section, update_view))
            self.active_section = section

    reader = FakeReader()
    viewer = TocFocusHarness(insertion_point, reader)
    event = FakeFocusEvent()

    BookViewerWindow.onTocTreeFocus(viewer, event)

    assert event.skipped
    assert event.focused
    assert reader.active_section is current_section
    assert reader.set_active_section_calls == [(current_section, False)]
    assert viewer.selected_sections == [current_section]
    assert viewer.insertion_point == insertion_point


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


@pytest.mark.parametrize("default_font_result", [True, False])
def test_set_content_sets_font_before_control_value(default_font_result):
    text = "intro \U0001d445\U0001d446"
    font = object()
    content_style = SimpleNamespace(Font=font)
    viewer = SetContentHarness(content_style)
    viewer.contentTextCtrl.default_font_result = default_font_result

    viewer.set_content(text)

    text_ctrl_value = TextCtrlPositionMap(text).to_text_ctrl_value()
    assert viewer.contentTextCtrl.value == text_ctrl_value
    expected_calls = [
        ("set_default_text_font", font),
        ("SetValue", text_ctrl_value),
    ]
    if not default_font_result:
        expected_calls.append(("set_all_text_font", font))
    expected_calls.append(("SetDefaultStyle", content_style))
    assert viewer.contentTextCtrl.calls[1 : 1 + len(expected_calls)] == expected_calls


def test_set_content_view_font_updates_existing_and_default_text_styles():
    font = object()
    content_style = SimpleNamespace(Font=font)
    viewer = SetContentHarness(content_style)

    viewer.set_content_view_font()

    assert viewer.contentTextCtrl.calls == [
        ("set_default_text_font", font),
        ("set_all_text_font", font),
        ("SetDefaultStyle", content_style),
    ]


class FakeZoomFont:
    def __init__(self, point_size):
        self.point_size = point_size

    def GetPointSize(self):  # noqa: N802
        return self.point_size

    def MakeLarger(self):  # noqa: N802
        return FakeZoomFont(self.point_size + 2)

    def MakeSmaller(self):  # noqa: N802
        return FakeZoomFont(self.point_size - 2)


class ZoomRecordingTextCtrl:
    def __init__(self, point_size=12, default_point_size=11, result=True):
        self.font = FakeZoomFont(point_size)
        self.default_style = SimpleNamespace(Font=FakeZoomFont(default_point_size))
        self.result = result
        self.calls = []

    def GetStyle(self, position, style):  # noqa: N802
        style.Font = self.font
        self.calls.append(("GetStyle", position))
        return True

    def GetDefaultStyle(self):  # noqa: N802
        self.calls.append(("GetDefaultStyle",))
        return self.default_style

    def set_all_text_point_size(self, point_size):
        self.calls.append(("set_all_text_point_size", point_size))
        return self.result


@pytest.mark.parametrize(
    ("direction", "expected_point_size", "expected_has_zoom"),
    [
        (1, 14, True),
        (-1, 10, True),
        (0, 11, False),
    ],
)
def test_text_zoom_changes_only_the_point_size(
    monkeypatch, direction, expected_point_size, expected_has_zoom
):
    text_ctrl = ZoomRecordingTextCtrl()
    viewer = SimpleNamespace(contentTextCtrl=text_ctrl, _has_text_zoom=False)
    announcements = []
    monkeypatch.setattr(book_viewer.wx, "TextAttr", lambda: SimpleNamespace(Font=None))
    monkeypatch.setattr(book_viewer.speech, "announce", announcements.append)

    BookViewerWindow.onTextCtrlZoom(viewer, direction)

    assert text_ctrl.calls[-1] == ("set_all_text_point_size", expected_point_size)
    assert viewer._has_text_zoom is expected_has_zoom
    assert len(announcements) == 1


def test_text_zoom_does_not_announce_when_formatting_fails(monkeypatch):
    text_ctrl = ZoomRecordingTextCtrl(result=False)
    viewer = SimpleNamespace(contentTextCtrl=text_ctrl, _has_text_zoom=False)
    announcements = []
    bells = []
    monkeypatch.setattr(book_viewer.wx, "TextAttr", lambda: SimpleNamespace(Font=None))
    monkeypatch.setattr(book_viewer.speech, "announce", announcements.append)
    monkeypatch.setattr(book_viewer.wx, "Bell", lambda: bells.append(True))

    BookViewerWindow.onTextCtrlZoom(viewer, 1)

    assert viewer._has_text_zoom is False
    assert announcements == []
    assert bells == [True]


@pytest.mark.skipif(sys.platform != "win32", reason="RichEdit is Windows-specific")
@pytest.mark.parametrize(
    ("method_name", "panel_method_name", "value"),
    [
        ("set_all_text_font", "set_all_text_font", object()),
        ("set_default_text_font", "set_default_text_font", object()),
        ("set_all_text_point_size", "set_all_text_point_size", 14),
    ],
)
def test_native_text_formatting_failure_uses_wx_fallback(
    monkeypatch, method_name, panel_method_name, value
):
    ctrl = ContentViewCtrl.__new__(ContentViewCtrl)
    ctrl.panel = SimpleNamespace(**{panel_method_name: lambda _value: False})
    fallback_calls = []
    warnings = []
    monkeypatch.setattr(
        ContentViewCtrlMixin,
        method_name,
        lambda _self, fallback_value: fallback_calls.append(fallback_value) or True,
    )
    monkeypatch.setattr(richedit.log, "warning", lambda *args: warnings.append(args))

    assert getattr(ctrl, method_name)(value)
    assert getattr(ctrl, method_name)(value)
    assert fallback_calls == [value, value]
    assert len(warnings) == 1


@pytest.mark.skipif(sys.platform != "win32", reason="RichEdit is Windows-specific")
@pytest.mark.parametrize(
    ("face_name", "accepted"),
    [
        ("A" * 29 + "\U0001f600", True),
        ("A" * 30 + "\U0001f600", False),
    ],
)
def test_native_font_formatter_counts_face_length_in_utf16_code_units(face_name, accepted):
    native_calls = []
    panel = SimpleNamespace(
        _set_all_text_font=lambda *args: native_calls.append(args) or 1,
        text_ctrl=SimpleNamespace(GetHandle=lambda: 1),
    )
    font = SimpleNamespace(
        IsOk=lambda: True,
        GetFaceName=lambda: face_name,
        GetPointSize=lambda: 12,
        GetWeight=lambda: book_viewer.wx.FONTWEIGHT_NORMAL,
    )

    result = richedit.WNDProcPanel._call_text_font_formatter(panel, panel._set_all_text_font, font)

    assert result is accepted
    assert len(native_calls) == int(accepted)
    if accepted:
        assert native_calls[0][2] == 31


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
