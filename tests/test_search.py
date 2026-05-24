from types import SimpleNamespace

import pytest

from bookworm.document import SINGLE_PAGE_DOCUMENT_PAGER, Section
from bookworm.document.operations import (
    SearchRequest,
    SearchResult,
    search_single_page_document,
)
from bookworm.gui.book_viewer import menubar as menubar_module
from bookworm.gui.book_viewer.core_dialogs import SearchResultsDialog
from bookworm.gui.book_viewer.menubar import SearchMenu
from bookworm.gui.components import PageRangeControl
from bookworm.structured_text import TextRange


class SearchRangeHarness:
    get_text_range = PageRangeControl.get_text_range
    _get_text_range_for_section = PageRangeControl._get_text_range_for_section


class SearchMenuHarness:
    _get_current_search_result_index = SearchMenu._get_current_search_result_index
    _highlight_search_result_from_dialog = (
        SearchMenu._highlight_search_result_from_dialog
    )
    _get_search_result_candidate = SearchMenu._get_search_result_candidate
    go_to_search_result = SearchMenu.go_to_search_result
    highlight_search_result = SearchMenu.highlight_search_result.__wrapped__

    def __init__(
        self,
        insertion_point,
        results,
        selection_range=None,
        last_search_index=None,
        line_ranges_by_page=None,
    ):
        self._latest_search_results = results
        self._last_search_index = last_search_index
        self._recent_search_term = "Android"
        self.pages = []
        self.selected = []
        self.reader = SimpleNamespace(current_page=0)
        self._line_ranges_by_page = line_ranges_by_page or {0: (0, 30)}

        def go_to_page(page):
            self.reader.current_page = page
            self.pages.append(page)

        self.reader.go_to_page = go_to_page
        self.view = SimpleNamespace(
            get_insertion_point=lambda: insertion_point,
            get_containing_line=lambda _pos: self._line_ranges_by_page[
                self.reader.current_page
            ],
            select_text=lambda start, end: self.selected.append((start, end)),
        )
        if selection_range is not None:
            self.view.get_selection_range = lambda: selection_range


class SearchResultsDialogHarness:
    onItemClick = SearchResultsDialog.onItemClick

    def __init__(self, focused_index, results, highlight_func):
        self._search_results = results
        self.highlight_func = highlight_func
        self.closed = False
        self.destroyed = False
        self.searchResultsListCtrl = SimpleNamespace(
            GetFocusedItem=lambda: focused_index,
        )

    def Close(self):  # noqa: N802
        self.closed = True

    def Destroy(self):  # noqa: N802
        self.destroyed = True


class FakeSectionChoice:
    def __init__(self, section):
        self.section = section

    def GetSelection(self):  # noqa: N802
        return object()

    def GetClientData(self, _item):  # noqa: N802
        return self.section


def test_single_page_section_search_range_covers_selected_section_subtree():
    root = Section(
        title="Document",
        pager=SINGLE_PAGE_DOCUMENT_PAGER,
        text_range=TextRange(0, 100),
    )
    selected_section = Section(
        title="Selected",
        pager=SINGLE_PAGE_DOCUMENT_PAGER,
        text_range=TextRange(10, 10),
    )
    child_section = Section(
        title="Child",
        pager=SINGLE_PAGE_DOCUMENT_PAGER,
        text_range=TextRange(30, 30),
    )
    next_section = Section(
        title="Next",
        pager=SINGLE_PAGE_DOCUMENT_PAGER,
        text_range=TextRange(70, 70),
    )
    root.append(selected_section)
    selected_section.append(child_section)
    root.append(next_section)
    control = SearchRangeHarness()
    control.doc = SimpleNamespace(toc_tree=root)
    control.sectionChoice = FakeSectionChoice(selected_section)

    assert control.get_text_range() == TextRange(10, 70)


def make_search_result(position, page=0, match_length=6):
    return SearchResult(
        excerpt="",
        page=page,
        position=position,
        section="",
        match_range=TextRange(position, position + match_length),
    )


def test_single_page_search_result_records_absolute_match_range():
    request = SearchRequest(
        term=r"Andr\w+",
        is_regex=True,
        case_sensitive=False,
        whole_word=False,
        text_range=TextRange(10, 24),
    )

    result = next(search_single_page_document("xx Android yy", request))[0]

    assert result.position == 13
    assert result.match_range == TextRange(13, 20)


def stub_search_navigation_feedback(monkeypatch):
    calls = SimpleNamespace(reading_events=[], navigation_sound=[], speech=[])
    monkeypatch.setattr(menubar_module, "_", lambda text: text, raising=False)
    monkeypatch.setattr(
        menubar_module.reading_position_change,
        "send",
        lambda *args, **kwargs: calls.reading_events.append((args, kwargs)),
    )
    monkeypatch.setattr(
        menubar_module.sounds,
        "navigation",
        SimpleNamespace(play=lambda: calls.navigation_sound.append(True)),
    )
    monkeypatch.setattr(
        menubar_module.speech,
        "announce",
        lambda *args, **kwargs: calls.speech.append((args, kwargs)),
    )
    return calls


@pytest.mark.parametrize(
    ("foreword", "insertion_point", "expected_position"),
    [
        (True, 5, 8),
        (False, 15, 8),
    ],
)
def test_search_result_navigation_uses_cursor_position_for_same_line_results(
    monkeypatch,
    foreword,
    insertion_point,
    expected_position,
):
    feedback = stub_search_navigation_feedback(monkeypatch)
    results = tuple(make_search_result(pos) for pos in (2, 8, 20))
    menu = SearchMenuHarness(insertion_point, results)

    menu.go_to_search_result(foreword=foreword)

    assert menu.pages == [0]
    assert menu.selected == [(expected_position, expected_position + 6)]
    assert menu._last_search_index == 1
    assert feedback.reading_events[0][1]["position"] == expected_position


@pytest.mark.parametrize(
    ("foreword", "expected_position", "expected_index"),
    [
        (True, 20, 2),
        (False, 2, 0),
    ],
)
def test_search_result_navigation_advances_from_selected_same_line_result(
    monkeypatch,
    foreword,
    expected_position,
    expected_index,
):
    feedback = stub_search_navigation_feedback(monkeypatch)
    results = tuple(make_search_result(pos) for pos in (2, 8, 20))
    menu = SearchMenuHarness(
        insertion_point=30,
        results=results,
        selection_range=results[1].match_range,
        last_search_index=1,
    )

    menu.go_to_search_result(foreword=foreword)

    assert menu.pages == [0]
    assert menu.selected == [(expected_position, expected_position + 6)]
    assert menu._last_search_index == expected_index
    assert feedback.reading_events[0][1]["position"] == expected_position


@pytest.mark.parametrize(
    ("foreword", "insertion_point", "last_search_index", "expected_last_index"),
    [
        (True, 30, 2, 2),
        (False, 30, 0, 0),
        (True, 25, None, None),
        (False, 0, None, None),
    ],
)
def test_search_result_navigation_stops_when_no_result_in_direction(
    monkeypatch,
    foreword,
    insertion_point,
    last_search_index,
    expected_last_index,
):
    feedback = stub_search_navigation_feedback(monkeypatch)
    results = tuple(make_search_result(pos) for pos in (2, 8, 20))
    selection_range = (
        results[last_search_index].match_range
        if last_search_index is not None
        else None
    )
    menu = SearchMenuHarness(
        insertion_point=insertion_point,
        results=results,
        selection_range=selection_range,
        last_search_index=last_search_index,
    )

    menu.go_to_search_result(foreword=foreword)

    assert menu.pages == []
    assert menu.selected == []
    assert menu._last_search_index == expected_last_index
    assert feedback.reading_events == []
    assert feedback.navigation_sound == [True]
    expected_speech = (
        "No next search result for 'Android'"
        if foreword
        else "No previous search result for 'Android'"
    )
    assert feedback.speech == [((expected_speech, True), {})]


def test_search_results_dialog_selection_updates_menu_search_index():
    results = tuple(make_search_result(pos) for pos in (2, 8, 20))
    menu = SearchMenuHarness(insertion_point=30, results=results)
    dialog = SearchResultsDialogHarness(
        focused_index=1,
        results=results,
        highlight_func=menu._highlight_search_result_from_dialog,
    )

    dialog.onItemClick(None)

    assert menu._last_search_index == 1
    assert menu.selected == [(8, 14)]
    assert dialog.closed
    assert dialog.destroyed


def test_zero_width_search_result_fallback_line_uses_target_page():
    result = make_search_result(position=5, page=1, match_length=0)
    menu = SearchMenuHarness(
        insertion_point=0,
        results=(result,),
        line_ranges_by_page={0: (0, 10), 1: (40, 60)},
    )

    menu.highlight_search_result(result)

    assert menu.pages == [1]
    assert menu.selected == [(40, 60)]
