from datetime import datetime, timedelta

import pytest

from bookworm.annotation import NoteTaker
from bookworm.database.models import *
from bookworm.document.uri import DocumentUri

from conftest import asset, reader


def test_notes_can_not_overlap(asset, reader):
    uri = DocumentUri.from_filename(asset("roman.epub"))
    reader.load(uri)
    annot = NoteTaker(reader)
    # This should succeed
    comment = annot.create(
        title="test", content="test", position=0, start_pos=0, end_pos=1
    )
    # check if it overlaps at start_pos 0, end_pos 1, page_number 0 and position 0
    assert annot.overlaps(0, 1, 0, 0) == True
    # Check if no selection with position 0 and page_number 0 overlaps with the existing annotation
    assert annot.overlaps(None, None, 0, 0)
    # This should not overlap
    assert annot.overlaps(None, None, 0, 2) == False


def test_notes_respect_sort_criteria(asset, reader):
    uri = DocumentUri.from_filename(asset("roman.epub"))
    reader.load(uri)
    # the shape of the list's elements is:
    # (title, content, page_number, position, start_pos, end_pos)
    notes = [
        ("first test", "test", 0, 0, 0, 1),
        ("second test", "test", 0, 1, 1, 2),
        ("third test", "test", 0, 5, 5, 10),
        ("fourth test", "test", 0, 11, 11, 15),
        ("fifth test", "test", 0, 16, 16, 20),
    ]        
    expected_titles = [x[0] for x in sorted(notes, key = lambda x: x[3])]
    annotator = NoteTaker(reader)
    for note in notes:
        annotator.create(
            title=note[0],
            content=note[1],
            page_number=note[2],
            position=note[3],
            start_pos=note[4],
            end_pos=note[5],
        )
    titles = [x.title for x in annotator.get_all(asc=True)]
    assert expected_titles == titles
