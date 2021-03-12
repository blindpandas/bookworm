# coding: utf-8

"""
Database models for `Bookworm`.
"""

from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import types
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
import db_magic as db
from bookworm.document_uri import DocumentUri
from bookworm.logger import logger


log = logger.getChild(__name__)



class DocumentUriDBType(types.TypeDecorator):
    """Provides sqlalchemy custom type for the DocumentUri."""

    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        return value.to_uri_string()

    def process_result_value(self, value, dialect):
        return DocumentUri.from_uri_string(value)


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
    uri = sa.Column(DocumentUriDBType(1024), nullable=False, unique=True, index=True)

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        instance = super().get_or_create(*args, **kwargs)
        session = cls.session()
        session.add(instance)
        session.commit()
        return instance


class Book(DocumentBase):

    @property
    def identifier(self):
        return self.uri.to_uri_string()


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
        return cls.query.order_by(cls.last_opened_on.desc()).limit(10).all()

    @classmethod
    def clear_all(cls):
        session = cls.session
        for item in cls.query.all():
            session.delete(item)
        session.commit()
