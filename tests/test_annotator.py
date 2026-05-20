from pathlib import Path
import shutil
from types import SimpleNamespace

from bookworm import config
from bookworm.annotation import AnnotationService, NoteTaker
from bookworm.annotation import annotation_gui
from bookworm.annotation.annotation_gui import AnnotationMenu
from bookworm.annotation.annotator import AnnotationSortCriteria, Quoter
from bookworm.database.models import *
from bookworm.document.uri import DocumentUri
from bookworm.structured_text import SemanticElementType, TextRange


def test_notes_can_not_overlap(asset, reader):
    uri = DocumentUri.from_filename(asset("roman.epub"))
    reader.load(uri)
    assert Book.query.count() == 1
    annot = NoteTaker(reader)
    # This should succeed
    annot.create(
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
        ("first test", "test", 0, 1, 1, 1),
        ("second test", "test", 0, 1, 1, 2),
        ("third test", "test", 0, 5, 5, 10),
        ("fourth test", "test", 0, 11, 11, 15),
        ("fifth test", "test", 0, 16, 16, 20),
    ]
    expected_titles = [x[0] for x in sorted(notes, key=lambda x: x[3])]
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
    # we append a note which is supposed to show up as first when ordered by position
    note = ("sixth test", "test", 0, 0, 0, 1)
    notes.append(note)
    annotator.create(
        title=note[0],
        content=note[1],
        page_number=note[2],
        position=note[3],
        start_pos=note[4],
        end_pos=note[5],
    )
    expected_titles = [x[0] for x in sorted(notes, key=lambda x: x[3])]
    titles = [
        x.title
        for x in annotator.get_all(
            asc=True, sort_criteria=AnnotationSortCriteria.Position
        )
    ]
    print(expected_titles)
    assert titles == expected_titles


def test_annotations_refer_to_same_document_in_different_path(asset, reader):
    path = Path(asset("roman.epub"))
    new_path = Path(path.parent, "test")
    new_path.mkdir(exist_ok=True)
    uri = DocumentUri.from_filename(asset("roman.epub"))
    reader.load(uri)
    annotator = NoteTaker(reader)
    annotator.create(title="test", content="test note", page_number=0)
    assert annotator.get_for_page(0).count() == 1
    reader.unload()
    new_file = shutil.copy(path, new_path)
    reader.load(DocumentUri.from_filename(new_file))
    assert annotator.get_for_page(0).count() == 1
    reader.unload()
    shutil.rmtree(new_path)


def test_comments_are_styled_on_initial_landing_page(asset, reader, view, monkeypatch):
    view.Bind = lambda *args, **kwargs: None
    view.add_load_handler = lambda func: None
    view.synchronise_menu = lambda *args, **kwargs: None
    view.contentTextCtrl.Bind = lambda *args, **kwargs: None
    view.contentTextCtrl.GetId = lambda: 1
    view.contentTextCtrl.EVT_CARET = object()

    service = AnnotationService(view)
    config.conf.spec.update(service.config_spec)
    config.conf.validate_and_write()
    uri = DocumentUri.from_filename(asset("roman.epub"))

    config.conf["annotation"][
        "audable_indication_of_annotations_when_navigating_text"
    ] = False

    reader.load(uri)
    NoteTaker(reader).create(title="test", content="test note")
    reader.unload()

    styled_positions = []
    monkeypatch.setattr(
        AnnotationService,
        "style_comment",
        lambda _view, position: styled_positions.append(position),
    )
    monkeypatch.setattr(AnnotationService, "style_bookmark", lambda *args, **kwargs: None)
    monkeypatch.setattr(AnnotationService, "style_highlight", lambda *args, **kwargs: None)

    reader.load(uri)

    assert styled_positions == [0]
    reader.unload()


def test_extending_highlight_to_before_image_preserves_range_stop(
    reader, view, tmp_path, monkeypatch
):
    html_path = tmp_path / "image.html"
    html_path.write_text(
        """
        <html>
            <head><title>Book</title></head>
            <body><p>before <img src="pic.png" alt="Chart"> after text</p></body>
        </html>
        """,
        encoding="utf-8",
    )
    reader.load(DocumentUri.from_filename(html_path))
    image_start, image_stop = reader.document.get_document_semantic_structure()[
        SemanticElementType.FIGURE
    ][0]
    existing_range = reader.view_to_storage_range(0, 2)
    expected_range = reader.view_to_storage_range(0, image_start)
    range_with_image = reader.view_to_storage_range(0, image_stop)
    quote = Quoter(reader).create(
        title="",
        content="be",
        start_pos=existing_range.start,
        end_pos=existing_range.stop,
    )
    view.get_selection_range = lambda: TextRange(1, image_start)
    view.get_text_by_range = lambda start, stop: reader.get_current_page_object().get_text()[
        start:stop
    ]
    service = SimpleNamespace(style_highlight=lambda *args, **kwargs: None)
    menu = SimpleNamespace(reader=reader, view=view, service=service)
    monkeypatch.setattr(annotation_gui.wx, "GetKeyState", lambda key: False)
    monkeypatch.setattr(annotation_gui.speech, "announce", lambda *args, **kwargs: None)

    AnnotationMenu.onQuoteSelection(menu, None)

    quote = Quoter(reader).get(quote.id)
    assert quote.end_pos == expected_range.stop
    assert quote.end_pos != range_with_image.stop
    assert reader.storage_to_view_range(
        quote.start_pos,
        quote.end_pos,
        quote.page_number,
    ).astuple() == (0, image_start)
    reader.unload()
