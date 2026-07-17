import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

import bookworm.annotation as annotation_module
from bookworm import config
from bookworm.annotation import AnnotationService, Bookmarker, NoteTaker, annotation_gui
from bookworm.annotation.annotation_gui import AnnotationMenu
from bookworm.annotation.annotator import AnnotationSortCriteria, Quoter
from bookworm.database.models import Book, Bookmark, Note, Quote
from bookworm.document.uri import DocumentUri
from bookworm.structured_text import (
    CURRENT_POSITION_MODEL_VERSION,
    LEGACY_CONTENT_HASH_VERSION,
    LEGACY_POSITION_MODEL_VERSION,
    SemanticElementType,
    TextRange,
)


def key_event(key_code):
    return SimpleNamespace(
        KeyCode=key_code,
        Skip=lambda: None,
        GetKeyCode=lambda: key_code,
        GetModifiers=lambda: 0,
    )


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

    legacy_note = annotator.create(title="legacy", content="legacy", position=0)
    legacy_note.position_version = None
    annotator.session.commit()

    assert legacy_note not in annotator.get_all()


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


def test_legacy_annotations_can_be_viewed_and_relocated(reader, view, tmp_path):
    current_path = tmp_path / "current.txt"
    current_path.write_text("alpha beta gamma delta", encoding="utf-8")
    reader.load(DocumentUri.from_filename(current_path))
    current_book_id = reader.current_book_record.id
    section = reader.active_section

    legacy_book = Book(
        title="Legacy copy",
        uri=DocumentUri.from_filename(tmp_path / "old.txt"),
        content_hash=reader.document.get_legacy_content_hash(),
        content_hash_version=LEGACY_CONTENT_HASH_VERSION,
    )
    session = Book.session()
    session.add(legacy_book)
    session.flush()
    bookmark = Bookmark(
        title="bookmark",
        page_number=0,
        position=1,
        section_title=section.title,
        section_identifier=section.unique_identifier,
        book_id=legacy_book.id,
        position_version=LEGACY_POSITION_MODEL_VERSION,
    )
    note = Note(
        title="note",
        content="note content",
        page_number=0,
        position=1,
        start_pos=None,
        end_pos=None,
        section_title=section.title,
        section_identifier=section.unique_identifier,
        book_id=legacy_book.id,
        position_version=LEGACY_POSITION_MODEL_VERSION,
    )
    quote = Quote(
        title="quote",
        content="quote content",
        page_number=0,
        position=1,
        start_pos=1,
        end_pos=2,
        section_title=section.title,
        section_identifier=section.unique_identifier,
        book_id=legacy_book.id,
        position_version=LEGACY_POSITION_MODEL_VERSION,
    )
    session.add_all((bookmark, note, quote))
    session.commit()

    bookmarker = Bookmarker(reader)
    note_taker = NoteTaker(reader)
    quoter = Quoter(reader)
    assert bookmarker.get_for_book() == []
    assert note_taker.get_for_book() == []
    assert quoter.get_for_book() == []
    assert bookmarker.get_for_book(include_unmigrated=True) == [bookmark]
    assert note_taker.get_for_book(include_unmigrated=True) == [note]
    assert quoter.get_for_book(include_unmigrated=True) == [quote]
    assert note in NoteTaker.get_all(include_unmigrated=True)
    assert quote in Quoter.get_all(include_unmigrated=True)

    view.insertion_point = 6
    view.selection_range = TextRange(6, 6)
    view.get_selection_range = lambda: view.selection_range
    with pytest.raises(ValueError, match="Select text"):
        quoter.relocate(quote.id)

    view.selection_range = TextRange(6, 10)
    expected_range = reader.view_to_storage_range(6, 10)
    bookmarker.relocate(bookmark.id)
    note_taker.relocate(note.id)
    quoter.relocate(quote.id)

    assert bookmark.book_id == current_book_id
    assert bookmark.position == reader.view_to_storage_position(6)
    for item in (bookmark, note, quote):
        assert item.position_version == CURRENT_POSITION_MODEL_VERSION
        assert item.book_id == current_book_id
    for item in (note, quote):
        assert item.position == expected_range.start
        assert (item.start_pos, item.end_pos) == expected_range.astuple()
    reader.unload()


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


def make_highlight_test_document(reader, tmp_path):
    html_path = tmp_path / "highlight.html"
    html_path.write_text(
        """
        <html>
            <head><title>Book</title></head>
            <body><p>alpha beta gamma delta</p></body>
        </html>
        """,
        encoding="utf-8",
    )
    reader.load(DocumentUri.from_filename(html_path))
    return reader.get_current_page_object().get_text()


def run_quote_selection(reader, view, monkeypatch, start, stop):
    view.get_selection_range = lambda: TextRange(start, stop)
    view.get_text_by_range = lambda selected_start, selected_stop: (
        reader.get_current_page_object().get_text()[selected_start:selected_stop]
    )
    style_calls = []
    service = SimpleNamespace(
        style_highlight=lambda *args, **kwargs: style_calls.append((args, kwargs))
    )
    menu = SimpleNamespace(reader=reader, view=view, service=service)
    monkeypatch.setattr(annotation_gui.wx, "GetKeyState", lambda key: False)
    monkeypatch.setattr(annotation_gui.speech, "announce", lambda *args, **kwargs: None)

    AnnotationMenu.onQuoteSelection(menu, None)

    return style_calls


def test_extending_highlight_backward_to_existing_stop_updates_existing_quote(
    reader, view, tmp_path, monkeypatch
):
    text = make_highlight_test_document(reader, tmp_path)
    old_start = text.index("gamma")
    old_stop = text.index(" delta")
    new_start = text.index("beta")
    quoter = Quoter(reader)
    old_storage_range = reader.view_to_storage_range(old_start, old_stop)
    quote = quoter.create(
        title="",
        content=text[old_start:old_stop],
        start_pos=old_storage_range.start,
        end_pos=old_storage_range.stop,
    )

    run_quote_selection(reader, view, monkeypatch, new_start, old_stop)

    quotes = quoter.get_for_page().all()
    assert len(quotes) == 1
    quote = quoter.get(quote.id)
    assert reader.storage_to_view_range(
        quote.start_pos,
        quote.end_pos,
        quote.page_number,
    ).astuple() == (new_start, old_stop)
    reader.unload()


def test_adjacent_highlight_before_existing_quote_creates_separate_quote(
    reader, view, tmp_path, monkeypatch
):
    text = make_highlight_test_document(reader, tmp_path)
    old_start = text.index("gamma")
    old_stop = text.index(" delta")
    adjacent_start = text.index("beta")
    quoter = Quoter(reader)
    old_storage_range = reader.view_to_storage_range(old_start, old_stop)
    quote = quoter.create(
        title="",
        content=text[old_start:old_stop],
        start_pos=old_storage_range.start,
        end_pos=old_storage_range.stop,
    )

    run_quote_selection(reader, view, monkeypatch, adjacent_start, old_start)

    quotes = quoter.get_for_page().all()
    assert len(quotes) == 2
    original_quote = quoter.get(quote.id)
    assert reader.storage_to_view_range(
        original_quote.start_pos,
        original_quote.end_pos,
        original_quote.page_number,
    ).astuple() == (old_start, old_stop)
    assert any(
        reader.storage_to_view_range(q.start_pos, q.end_pos, q.page_number).astuple()
        == (adjacent_start, old_start)
        for q in quotes
    )
    reader.unload()


def test_bookmark_navigation_uses_selected_line_edge(
    asset, reader, view, monkeypatch
):
    def get_containing_line(pos):
        start = text.rfind("\n", 0, pos) + 1
        stop = text.find("\n", pos)
        return start, len(text) if stop == -1 else stop

    uri = DocumentUri.from_filename(asset("roman.epub"))
    config.conf.spec.update(AnnotationService.config_spec)
    config.conf.validate_and_write()
    config.conf["annotation"]["select_bookmarked_line_on_jumping"] = True
    reader.load(uri)
    service = AnnotationService.__new__(AnnotationService)
    service.view = view
    service.reader = reader
    service._AnnotationService__state = {}
    text = reader.get_current_page_object().get_text()
    first_line_start = text.find("\n") + 1
    first_line_stop = text.find("\n", first_line_start)
    bookmark_position = first_line_start + 1
    next_bookmark_position = text.find("\n", first_line_stop + 1) + 1
    bookmarker = Bookmarker(reader)
    bookmarker.create(
        title="first",
        position=reader.view_to_storage_position(bookmark_position),
    )
    bookmarker.create(
        title="second",
        position=reader.view_to_storage_position(next_bookmark_position),
    )
    view.selection_range = TextRange(0, 0)
    view.selected_range = None
    view.get_selection_range = lambda: view.selection_range
    view.get_containing_line = get_containing_line

    def select_text(start, stop):
        view.selected_range = (start, stop)
        view.selection_range = TextRange(start, stop)
        view.insertion_point = start

    view.select_text = select_text
    monkeypatch.setattr(
        annotation_module.sounds,
        "navigation",
        SimpleNamespace(play=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        annotation_module.speech,
        "announce",
        lambda *args, **kwargs: None,
    )

    service.onKeyUp(key_event(annotation_gui.wx.WXK_F2))
    first_selected_range = view.selected_range
    service.onKeyUp(key_event(annotation_gui.wx.WXK_F2))

    assert first_selected_range == get_containing_line(bookmark_position)
    assert view.selected_range == get_containing_line(next_bookmark_position)
    reader.unload()


def test_next_highlight_navigation_uses_nearest_start_position(
    asset, reader, view, monkeypatch
):
    uri = DocumentUri.from_filename(asset("roman.epub"))
    reader.load(uri)
    service = AnnotationService.__new__(AnnotationService)
    service.view = view
    service.reader = reader
    service._AnnotationService__state = {}
    view.selection_range = TextRange(0, 0)
    view.selected_range = None
    view.get_selection_range = lambda: view.selection_range
    view.select_text = lambda start, stop: setattr(view, "selected_range", (start, stop))
    monkeypatch.setattr(
        annotation_module.sounds,
        "navigation",
        SimpleNamespace(play=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        annotation_module.speech,
        "announce",
        lambda *args, **kwargs: None,
    )

    late_range = reader.view_to_storage_range(50, 60)
    early_range = reader.view_to_storage_range(10, 20)
    quoter = Quoter(reader)
    quoter.create(
        title="late",
        content="late",
        start_pos=late_range.start,
        end_pos=late_range.stop,
    )
    quoter.create(
        title="early",
        content="early",
        start_pos=early_range.start,
        end_pos=early_range.stop,
    )

    service.onKeyUp(key_event(annotation_gui.wx.WXK_F9))

    assert view.insertion_point == 10
    assert view.selected_range == (10, 20)
    reader.unload()
