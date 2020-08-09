# coding: utf-8

from enum import IntEnum, auto
from dataclasses import dataclass, field, astuple
from typing import Tuple
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from bookworm.logger import logger
from bookworm.database import Book, db
from bookworm.database.models import Book
from .annotation_models import Bookmark, Note, Quote


log = logger.getChild(__name__)


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
        self.session = self.model.session

    def get_book_by_identifier(self, ident):
        return Book.query.filter(Book.identifier == ident).one_or_none()

    @property
    def current_book(self):
        if not self.reader.ready:
            return
        ident = self.reader.document.identifier
        book = self.get_book_by_identifier(ident)
        if book is None:
            book = Book(
                title=self.reader.current_book.title,
                identifier=ident,
                file_path=self.reader.document.filename,
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
        page_number = page_number or self.reader.current_page
        return self.model.query.filter_by(page_number=page_number)

    def get_for_section(self, section_ident=None, asc=False):
        section_ident = section_ident or self.reader.active_section.unique_identifier
        return self.model.query.filter_by(section_identifier=section_ident)

    def get(self, item_id):
        return self.model.query.get(item_id)

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


class NoteTaker(TaggedAnnotator):
    """Comments."""

    model = Note


class Quoter(TaggedAnnotator):
    """Highlights."""

    model = Quote
