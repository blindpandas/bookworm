import pytest

from bookworm.annotation import NoteTaker
from bookworm.annotation.annotator import AnnotationOverlapsError
from bookworm.database.models import * 
from bookworm.document.uri import DocumentUri

from conftest import asset, reader

def test_notes_can_not_overlap(asset, reader):
    uri = DocumentUri.from_filename(asset('roman.epub'))
    reader.load(uri)
    annot = NoteTaker(reader)
    # This should succeed
    comment = annot.create(title='test', content="test", position=0, start_pos=0, end_pos=1)
    with pytest.raises(AnnotationOverlapsError):
        comment = annot.create(title='test', content="test", position=0, start_pos=0, end_pos=1)
    with pytest.raises(AnnotationOverlapsError):
        comment = annot.create(title="", content="other test", position=0)
    # This should also succeed, since we're out of the range of the first defined comment
    comment = annot.create(title="", content="Second note", position=2)
