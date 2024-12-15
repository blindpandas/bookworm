from pathlib import Path

import pytest

from bookworm.config import setup_config
from bookworm.database import init_database
from bookworm.document.elements import Section
from bookworm.reader import EBookReader

@pytest.fixture(scope="function", autouse=True)
def asset():
    yield lambda filename: str(Path(__file__).parent / "assets" / filename)


class DummyTextCtrl:
    def SetFocus(self):
        pass
        

class DummyView:
    """Represents a mock for the bookworm view"""
    def __init__(self):
        self.title = ""
        self.toc_tree = None
        self.input_result = ""
        self.insertion_point = 0
        self.state_on_section_change: Section = None
        self.contentTextCtrl = DummyTextCtrl()
    
    def add_toc_tree(self, tree):
        self.toc_tree = tree

    def set_text_direction(self, direction):
        pass

    def set_title(self, title):
        self.title = title

    def get_insertion_point(self):
        return self.insertion_point
        
    def set_state_on_section_change(self, value: Section) -> None:
        self.state_on_section_change = value

    def set_state_on_page_change(self, page):
        pass

    def set_insertion_point(self, point: int) -> None:
        self.insertion_point = point

    def go_to_position(self, start: int, end: int) -> None:
        self.set_insertion_point(start)
    
    def go_to_webpage(self, url: str) -> None:
        pass

    def show_html_dialog(self, markup: str, title: str) -> None:
        pass

@pytest.fixture()
def text_ctrl():
    yield DummyTextCtrl()

@pytest.fixture
def view(text_ctrl):
    v = DummyView()
    v.contentTextCtrl = text_ctrl
    yield v

@pytest.fixture()
def reader(view):
    setup_config()
    engine = init_database(url="sqlite:///test.db")
    reader = EBookReader(view)
    yield reader
    engine.dispose()
    Path("test.db").unlink()