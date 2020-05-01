# coding: utf-8

from bookworm.logger import logger
from bookworm.utils import cached_property
from bookworm.database import db
from bookworm.database.models import Book, Bookmark, Note


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

    @cached_property
    def current_book(self):
        ident = self.reader.document.identifier
        book = self.get_book_by_identifier(ident)
        if book is None:
            book = Book(title=self.reader.current_book.title, identifier=ident)
            self.session.add(book)
            self.session.commit()
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
        self.session.add(self.model(**kwargs))
        self.session.commit()

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
        self.session.delete(self.get(item_id))
        self.session.commit()

    def update(self, item_id, **kwargs):
        item = self.get(item_id)
        if item is None:
            raise ValueError(f"There is no record with id={item_id}.")
        for attr, value in kwargs.items():
            setattr(item, attr, value)
        self.session.commit()


class Bookmarker(Annotator):
    """Bookmarks."""

    model = Bookmark


class NoteTaker(Annotator):
    """Notes."""

    model = Note
