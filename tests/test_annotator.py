import pytest

from bookworm.annotation import NoteTaker
from bookworm.database.models import * 
from bookworm.document.uri import DocumentUri

from conftest import asset, reader

def test_notes_can_not_overlap(asset, reader):
    uri = DocumentUri.from_filename(asset('roman.epub'))
    reader.load(uri)
    annot = NoteTaker(reader)
    # This should succeed
    comment = annot.create(title='test', content="test", position=0, start_pos=0, end_pos=1)
    # check if it overlaps at start_pos 0, end_pos 1, page_number 0 and position 0
    assert annot.overlaps(0, 1, 0, 0) == True
    # Check if no selection with position 0 and page_number 0 overlaps with the existing annotation
    assert annot.overlaps(None, None, 0, 0)
    # This should not overlap
    assert annot.overlaps(None, None, 0, 2) == False
