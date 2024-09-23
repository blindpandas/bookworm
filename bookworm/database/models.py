# coding: utf-8

"""
Database models for `Bookworm`.
"""

from datetime import datetime
import re

import sqlalchemy as sa
from sqlalchemy import types
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import class_mapper, mapper, Query, scoped_session, declarative_base

from bookworm.document.uri import DocumentUri
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


class _QueryProperty(object):
    """Convenience property to query a model."""

    def __get__(self, obj, type):
        try:
            mapper = class_mapper(type)
            if mapper:
                return Query(mapper, session=type.session())
        except UnmappedClassError:
            return None

class Model:
    id = sa.Column(sa.Integer, primary_key=True)
    query = _QueryProperty()

    @declared_attr
    def __tablename__(cls) -> str:
        """Taken from db_magic"""
        """Convert CamelCase class name to underscores_between_words 
        table name."""
        name = cls.__name__
        return name[0].lower() + re.sub(
            r"([A-Z])", lambda m: "_" + m.group(0).lower(), name[1:]
        )


Base = declarative_base(cls=Model)


class DocumentBase(Base, GetOrCreateMixin):
    __abstract__ = True
    __tablename__ = "document_base"
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String(512), nullable=False)
    uri = sa.Column(DocumentUriDBType(1024), nullable=False, unique=True, index=True)

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        instance = super().get_or_create(*args, **kwargs)
        session = cls.session()
        session.add(instance)
        session.commit()
        return instance


class Book(DocumentBase):
    __tablename__ = "book"
    
    @property
    def identifier(self):
        return self.uri.to_uri_string()


class DocumentPositionInfo(DocumentBase):
    __tablename__ = "document_position_info"
    last_page = sa.Column(sa.Integer, default=0)
    last_position = sa.Column(sa.Integer, default=0)

    def get_last_position(self):
        return (self.last_page, self.last_position)

    def save_position(self, page, pos):
        self.last_page = page
        self.last_position = pos
        self.session.commit()


class RecentDocument(DocumentBase):
    __tablename__ = "recent_document"
    last_opened_on = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def record_open(self):
        self.last_opened_on = datetime.utcnow()
        self.session.commit()

    @classmethod
    def get_recents(cls, limit=10):
        return cls.query.order_by(cls.last_opened_on.desc()).limit(limit).all()

    @classmethod
    def clear_all(cls):
        session = cls.session
        for item in cls.query.all():
            session.delete(item)
        session.commit()


class PinnedDocument(DocumentBase):
    __tablename__ = "pinned_document"
    last_opened_on = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_pinned = sa.Column(sa.Boolean, default=False)
    pinning_order = sa.Column(sa.Integer, default=0)

    @classmethod
    def get_pinned(cls, limit=50):
        return (
            cls.query.filter(cls.is_pinned == True)
            .order_by(cls.last_opened_on.desc())
            .order_by(cls.pinning_order.desc())
            .limit(limit)
            .all()
        )

    def pin(self):
        if self.is_pinned:
            return
        self.is_pinned = True
        self.session.commit()

    def unpin(self):
        if not self.is_pinned:
            return
        self.is_pinned = False
        self.session.commit()

    @classmethod
    def clear_all(cls):
        session = cls.session
        for item in cls.query.all():
            session.delete(item)
        session.commit()
