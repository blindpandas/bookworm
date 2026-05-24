from types import SimpleNamespace

from bookworm.document import SINGLE_PAGE_DOCUMENT_PAGER, Section
from bookworm.gui.components import PageRangeControl
from bookworm.structured_text import TextRange


class SearchRangeHarness:
    get_text_range = PageRangeControl.get_text_range
    _get_text_range_for_section = PageRangeControl._get_text_range_for_section


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
