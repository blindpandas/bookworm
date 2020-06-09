# coding: utf-8

from dataclasses import dataclass, field
from typing import Tuple
from enum import Enum, auto
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from bookworm.logger import logger
from bookworm.utils import cached_property
from bookworm.database import db
from bookworm.database.models import Book
from .annotation_models import Bookmark, Note, Quote


log = logger.getChild(__name__)


class Annotator:
    """Controller for annotations."""

    model = None
    """The model to act upon."""

    def __init__(self, reader):
        self.reader = reader
        self.session = self.model.session

    def get_book_by_identifier(self, ident):
        return Book.query.filter(Book.identifier == ident).one_or_none()

    @property
    def current_book(self):
        ident = self.reader.document.identifier
        book = self.get_book_by_identifier(ident)
        if book is None:
            book = Book(title=self.reader.current_book.title, identifier=ident)
            session = self.session()
            try:
                session.add(book)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                session.close()
                log.exception(f"An error occured while creating a new book: {e.args}")
                # XXX: Fix this
                return self.get_book_by_identifier(ident)
        return book

    def create(self, **kwargs):
        kwargs.update(
            dict(
                book_id=self.current_book.id,
                page_number=self.reader.current_page,
                section_title=self.reader.active_section.title,
                section_identifier=self.reader.active_section.unique_identifier,
            )
        )
        annot = self.model(**kwargs)
        session = self.session()
        try:
            session.add(annot)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            session.close()
            log.exception(f"An error occured while creating a new annotation: {e.args}")
        return annot

    def get(self, item_id):
        return self.model.query.get(item_id)

    def get_list(self, asc=False):
        sort_func = getattr(self.model.page_number, "asc" if asc else "desc")
        return self.model.query.filter(self.model.book == self.current_book).order_by(
            sort_func()
        )

    def get_for_page(self, page_number=None, asc=False):
        page_number = page_number or self.reader.current_page
        return self.get_list(asc).filter_by(page_number=page_number)

    def get_for_section(self, section_ident=None, asc=False):
        section_ident = section_ident or self.reader.active_section.unique_identifier
        return self.get_list(asc).filter_by(section_identifier=section_ident)

    def delete(self, item_id):
        session = self.session()
        try:
            session.delete(self.get(item_id))
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            session.close()
            log.exception(f"An error occured while deleting annotation: {e.args}")

    def update(self, item_id, **kwargs):
        item = self.get(item_id)
        if item is None:
            raise ValueError(f"There is no record with id={item_id}.")
        for attr, value in kwargs.items():
            setattr(item, attr, value)
        session = self.session()
        try:
            session.add(item)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            session.close()
            log.exception(f"An error occured while updating annotation: {e.args}")


class Bookmarker(Annotator):
    """Bookmarks."""

    model = Bookmark


class FilterableAnnotator(Annotator):
    """Adds filtering."""

    def filter(self, filter_opts):
        """Filter based on filteropts."""
        # Primary query
        q = None
        if filter_opts.tag:
            q = self.model.query.filter_by(self.model.Tag.id == tag_id)
        if filter_opts.book:
            if q is None:
                q = self.model.query
            q = q.filter_by(book_id=filter_opts.book)
            # Secondary criteria
            if filter_opts.secondary_filter is AnnotationFilteringOptions.SecondaryFilteringCriteria.page_range:
                start, end = filter_opts.page_range
                q = q.filter(sa.between(self.model.page_number, start, end))
            elif filter_opts.secondary_filter is AnnotationFilteringOptions.SecondaryFilteringCriteria.section:
                q = q.filter_by(section_identifier=section_identifier)
        return q


class NoteTaker(FilterableAnnotator):
    """Comments."""

    model = Note


class Quoter(FilterableAnnotator):
    """Highlights."""

    model = Quote


@dataclass
class AnnotationFilteringOptions:
    """Filter annotation using several criteria."""

    class SecondaryFilteringCriteria(Enum):
        page_range = auto
        section = auto()

    tag_id: int
    book_id: int
    secondary_filter: SecondaryFilteringCriteria
    page_range: Tuple[int, int]
    section_id: int
