# coding: utf-8

from dataclasses import astuple, dataclass
from enum import IntEnum, auto
from typing import Optional

import sqlalchemy as sa

from bookworm import config
from bookworm.database.models import Book, Bookmark, Note, Quote
from bookworm.logger import logger

log = logger.getChild(__name__)
# The bakery caches query objects to avoid recompiling them into strings in every call

@dataclass
class AnnotationFilterCriteria:
    book_id: int = 0
    tag: str = ""
    section_title: str = ""
    content_snip: str = ""

    def any(self):
        return any(astuple(self))

    def filter_query(self, model, query):
        if not self.any():
            return query
        clauses = []
        if self.book_id is not None:
            clauses.append(model.book_id == self.book_id)
        if self.tag:
            clauses.append(model.tags.contains(self.tag))
        if self.section_title:
            clauses.append(model.section_title == self.section_title)
        if self.content_snip:
            clauses.append(model.text_column.ilike(f"%{self.content_snip}%"))
        return query.filter(sa.and_(*clauses))


class AnnotationSortCriteria(IntEnum):
    Null = auto()
    Date = auto()
    Page = auto()
    Book = auto()

    def sort_query(self, model, query, asc=True):
        if self is AnnotationSortCriteria.Null:
            return query
        sort_fn = sa.asc if asc else sa.desc
        if self is AnnotationSortCriteria.Date:
            return query.order_by(
                sort_fn(sa.func.coalesce(model.date_updated, model.date_created))
            )
        elif self is AnnotationSortCriteria.Page:
            return query.order_by(sort_fn(model.page_number))
        elif self is AnnotationSortCriteria.Book:
            return query.order_by(sort_fn(model.book_id))


class Annotator:
    """Controller for annotations."""

    model = None
    """The model to act upon."""

    def __init__(self, reader):
        self.reader = reader
        self.session = self.model.session()

    def get_book_by_uri(self, uri):
        return Book.query.filter(Book.uri == uri).one_or_none()

    @property
    def current_book(self):
        if not self.reader.ready:
            return
        current_uri = self.reader.document.uri
        book = self.get_book_by_uri(current_uri)
        if book is None:
            book = Book(
                title=self.reader.current_book.title,
                uri=self.reader.document.uri,
            )
            self.session.add(book)
            self.session.commit()
            self.session.refresh(book)
        return book

    @classmethod
    def get_books_for_model(cls):
        return (
            Book.query.filter(Book.id.in_(sa.select([cls.model.book_id])))
            .order_by(Book.title.asc())
            .all()
        )

    def get_sections(self):
        return (
            self.model.session.query(self.model.section_title)
            .distinct()
            .filter(self.model.book == self.current_book)
            .order_by(self.model.page_number)
            .all()
        )

    @classmethod
    def get_all(
        cls,
        filter_criteria=None,
        sort_criteria=AnnotationSortCriteria.Date,
        asc=False,
    ):
        model = cls.model
        query = model.query
        if filter_criteria is not None:
            query = filter_criteria.filter_query(model, query)
        return sort_criteria.sort_query(model, query, asc=asc).all()

    def get_for_book(
        self, filter_criteria=None, sort_criteria=AnnotationSortCriteria.Page, asc=True
    ):
        filter_criteria = filter_criteria or AnnotationFilterCriteria()
        filter_criteria.book_id = self.current_book.id
        return self.get_all(
            filter_criteria=filter_criteria, sort_criteria=sort_criteria, asc=asc
        )

    def get_for_page(self, page_number=None, asc=False):
        return self.model.query.filter_by(
            book_id=self.current_book.id,
            page_number=page_number or self.reader.current_page,
        )

    def get_for_section(self, section_ident=None, asc=False):
        section_ident = section_ident or self.reader.active_section.unique_identifier
        return self.model.query.filter_by(
            book_id=self.current_book.id, section_identifier=section_ident
        )

    def get(self, item_id):
        return self.model.query.get(item_id)

    
    def get_first_after(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.position > pos,
            ),
            model.page_number > page_number,
        )
        return (
            self.session.query(model)
            .filter_by(book_id=self.current_book.id)
            .filter(sa.or_(*clauses))
            .order_by(model.page_number.asc(), model.position.asc())
            .first()
        )

    def get_first_before(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.position < pos,
            ),
            model.page_number < page_number,
        )
        return (
            self.session.query(model)
            .filter_by(book_id=self.current_book.id)
            .filter(sa.or_(*clauses))
            .order_by(model.page_number.desc())
            .order_by(model.position.desc())
            .first()
        )

    def create(self, **kwargs):
        if not self.reader.document.is_single_page_document():
            section_title = self.reader.active_section.title
        else:
            section_title = self.reader.document.get_section_at_position(
                self.reader.view.get_insertion_point()
            ).title
        kwargs.update(
            dict(
                book_id=self.current_book.id,
                page_number=self.reader.current_page,
                section_title=section_title,
                section_identifier=self.reader.active_section.unique_identifier,
            )
        )
        annot = self.model(**kwargs)
        self.session.add(annot)
        self.session.commit()
        return annot

    def update(self, item_id, **kwargs):
        item = self.get(item_id)
        if item is None:
            raise LookupError(f"There is no record with id={item_id}.")
        for attr, value in kwargs.items():
            setattr(item, attr, value)
        self.session.add(item)
        self.session.commit()

    def delete(self, item_id):
        self.session.delete(self.get(item_id))
        self.session.commit()


class Bookmarker(Annotator):
    """Bookmarks."""

    model = Bookmark


class TaggedAnnotator(Annotator):
    """Annotations which can be tagged."""

    @classmethod
    def get_tags(cls):
        cls.delete_orphan_tags()
        return [
            tag.title for tag in cls.model.Tag.query.order_by(cls.model.Tag.title).all()
        ]

    @classmethod
    def delete_orphan_tags(cls):
        session = cls.model.session()
        orphan_tags = [tag for tag in cls.model.Tag.query if len(tag.items) == 0]
        for otag in orphan_tags:
            session.delete(otag)
        session.commit()

class PositionedAnnotator(TaggedAnnotator):
    """Annotations which are positioned on a specific text range"""

    def overlaps(self, start: Optional[int], end: Optional[int], page_number: int, position: int) -> bool:
        """
        Determines whether an annotation overlaps with  a given position
        The criterias used to check for the position are the following:
        - If a selection is present, represented by start and end, then it is checked
        - If no selection is present the insertion point is used to determine if the annotation overlaps
        """
        model = self.model
        clauses = [
            sa.and_(
                model.start_pos.is_not(None),
                model.end_pos.is_not(None),
                model.start_pos == start,
                model.end_pos == end,
                model.page_number == page_number,
            ),
            sa.and_(
                model.page_number == page_number,
                model.position == position
            ),
            sa.and_(
                model.start_pos.is_not(None),
                model.end_pos.is_not(None),
                model.page_number == page_number,
                sa.or_(
                    sa.and_(
                        model.start_pos == position,
                        model.end_pos == position,
                    ),
                    sa.and_(
                        model.start_pos <= position,
                        model.end_pos >= position,
                    )
                )
            )
        ]
        return self.session.query(model).filter_by(book_id = self.current_book.id).filter(sa.or_(*clauses)).one_or_none() is not None


class NoteTaker(PositionedAnnotator):
    """Comments."""

    model = Note

    def update_ranges(self, page) -> None:
        """
        Start_pos and end_poss are None whenever the comments handle the whole text
        Since there is currently no way to dynamically set the correct values at runtime, we'll handle it here
        """
        for note in self.session.query(self.model).filter_by(book_id=self.current_book.id).filter(self.model.start_pos == None, self.model.end_pos == None, self.model.page_number == self.reader.current_page).all():
            start_pos, end_pos = self.reader.view.get_containing_line(note.position)
            note.start_pos = start_pos
            note.end_pos = end_pos - 1
            self.session.add(note)
        self.session.commit()
    
    def get_for_selection(self, start: int, end: int):
        model = self.model
        return self.session.query(model).filter_by(book_id = self.current_book.id).filter(model.start_pos == start, model.end_pos == end, model.page_number == self.reader.current_page).one_or_none()

    def get_first_after(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                # sa.or_(
                model.start_pos > pos,
                model.start_pos.is_not(None),
                # ),
            ),
            sa.and_(
                model.page_number == page_number,
                model.position > pos,
            ),
            sa.and_(
                model.page_number == page_number,
                model.end_pos.is_(None),
                model.position > pos,
            ),
            model.page_number > page_number,
        )
        return (
            self.session.query(model)
            .filter_by(book_id=self.current_book.id)
            .filter(sa.or_(*clauses))
            .order_by(
                model.page_number.asc(),
                sa.nulls_first(model.start_pos.asc()),
                sa.nulls_first(model.end_pos.asc()),
                model.position.asc(),
            )
            .first()
        )

    def get_first_before(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.start_pos < pos,
                model.start_pos.is_not(None),
            ),
            sa.and_(
                model.page_number == page_number,
                model.position  < pos,
                model.start_pos.is_(None)
            ),
            model.page_number < page_number,
        )
        return (
            self.session.query(model)
            .filter_by(book_id=self.current_book.id)
            .filter(sa.or_(*clauses))
            .order_by(model.page_number.desc())
            .order_by(sa.nulls_last(model.end_pos.desc()))
            .first()
        )

class Quoter(TaggedAnnotator):
    """Highlights."""

    model = Quote

    def get_first_after(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.start_pos > pos,
            ),
            model.page_number > page_number,
        )
        return (
            self.session.query(model)
            .filter_by(book_id=self.current_book.id)
            .filter(sa.or_(*clauses))
            .first()
        )

    def get_first_before(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.end_pos < pos,
            ),
            model.page_number < page_number,
        )
        return (
            self.session.query(model)
            .filter_by(book_id=self.current_book.id)
            .filter(sa.or_(*clauses))
            .order_by(model.page_number.desc())
            .order_by(model.end_pos.desc())
            .first()
        )
