# coding: utf-8

"""
Database models for `Bookworm`.
"""

from datetime import datetime
from sqlalchemy.orm import synonym
import db_magic as db


class GetOrCreateMixin:
    """Adds the `get_or_create` method to a sqlalchemy Model class."""

    @classmethod
    def get_or_create(cls, **kwargs):
        obj = cls.query.filter_by(**kwargs).one_or_none()
        if obj is not None:
            return obj
        return cls(**kwargs)


class DocumentBase(db.Model, GetOrCreateMixin):
    __abstract__ = True
    title = db.string(512, nullable=False)
    uri = db.string(1024, nullable=False, unique=True)


class Book(DocumentBase):
    identifier = db.string(512, unique=True, nullable=False)


class DocumentPositionInfo(DocumentBase):
    last_page = db.integer(default=0)
    last_position = db.integer(default=0)

    def get_last_position(self):
        return (self.last_page, self.last_position)

    def save_position(self, page, pos):
        self.last_page = page
        self.last_position = pos
        self.session.commit()


class RecentDocument(DocumentBase):
    last_opened_on = db.date_time(default=datetime.now, onupdate=datetime.now)

    def record_open(self):
        self.last_opened_on = datetime.now()
        self.session.commit()

    @classmethod
    def get_recents(cls, limit=10):
        return cls.query.order_by(cls.last_opened_on.asc()).limit(10).all()

    @classmethod
    def clear_all(cls):
        session = cls.session
        for item in cls.query.all():
            session.delete(item)
        session.commit()
