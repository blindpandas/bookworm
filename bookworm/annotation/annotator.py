# coding: utf-8

from dataclasses import dataclass, field
from typing import Tuple
from enum import Enum, auto
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from bookworm.logger import logger
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
            self.session.add(book)
            self.session.commit()
            self.session.refresh(book)
        return book

    @classmethod
    def get_sections(cls):
        return cls.model.session.query(cls.model.section_title).distinct().all()

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
        try:
            self.session.delete(self.get(item_id))
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            log.exception(f"An error occured while deleting annotation: {e.args}")

    def update(self, item_id, **kwargs):
        item = self.get(item_id)
        if item is None:
            raise ValueError(f"There is no record with id={item_id}.")
        for attr, value in kwargs.items():
            setattr(item, attr, value)
        try:
            self.session.add(item)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            log.exception(f"An error occured while updating annotation: {e.args}")


class Bookmarker(Annotator):
    """Bookmarks."""

    model = Bookmark


class TaggedAnnotator(Annotator):
    @classmethod
    def get_tags(cls):
        session = cls.model.session()
        orphan_tags = [tag for tag in cls.model.Tag.query if len(tag.items) == 0]
        for otag in orphan_tags:
            session.delete(otag)
        session.commit()
        return [tag.title for tag in cls.model.Tag.query.all()]

    @classmethod
    def get_filtered(cls, tag, section_title, content, *, clauses=()):
        model = cls.model
        clauses = list(clauses)
        if tag:
            clauses.append(model.tags.contains(tag))
        if section_title:
            clauses.append(model.section_title == section_title)
        if content:
            clauses.append(model.content.ilike(f"%{content}%"))
        return model.query.filter(sa.and_(*clauses))

    def get_filtered_for_book(self, *args):
        return self.get_filtered(*args, clauses=(self.model.book == self.current_book,))


class NoteTaker(TaggedAnnotator):
    """Comments."""

    model = Note


class Quoter(TaggedAnnotator):
    """Highlights."""

    model = Quote
