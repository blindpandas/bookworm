# coding: utf-8

"""
Database models for `Bookworm`.
"""

from datetime import datetime
import re

import sqlalchemy as sa
from sqlalchemy import types
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred, relationship, synonym, class_mapper, mapper, Query, scoped_session, declarative_base

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

# annotation models

class TaggedMixin:
    """Provides a generic many-to-many relationship
    to a  dynamically generated tags table  using
    the `table-per-related` pattern.

    .. admonition::: the dynamically generated table is shared by this model
     class and all it's subclasses.

     Adapted from oy-cms.
     Copyright (c) 2018 Musharraf Omer
    """

    @staticmethod
    def _prepare_association_table(table_name, remote1, remote2):
        return sa.Table(
            table_name,
            Base.metadata,
            sa.Column(f"{remote1}_id", sa.Integer, sa.ForeignKey(f"{remote1}.id")),
            sa.Column(f"{remote2}_id", sa.Integer, sa.ForeignKey(f"{remote2}.id")),
        )

    @declared_attr
    def tags(cls):
        if not hasattr(cls, "Tag"):
            # Create the Tag model
            tag_attrs = {
                "id": sa.Column(sa.Integer, primary_key=True),
                "title": sa.Column(sa.String(512), nullable=False, unique=True, index=True),
                "items": relationship(
                    cls,
                    secondary=lambda: cls.__tags_association_table__,
                    backref="related_tags",
                ),
            }
            cls.Tag = type(
                f"{cls.__name__}Tag", (GetOrCreateMixin, Base), tag_attrs
            )
            # The many-to-many association table
            cls.__tags_association_table__ = cls._prepare_association_table(
                table_name=f"{cls.__tablename__}s_tags",
                remote1=cls.__tablename__,
                remote2=cls.Tag.__tablename__,
            )
        return association_proxy(
            "related_tags",
            "title",
            creator=lambda t: cls.Tag.get_or_create(title=t.lower()),
        )


class AnnotationBase(Base):
    __abstract__ = True
    __tablename__ = "annotation_base"
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String(255), nullable=False)
    page_number = sa.Column(sa.Integer, nullable=False)
    position = sa.Column(sa.Integer, nullable=False, default=0)
    section_title = sa.Column(sa.String(1024), nullable=False)
    section_identifier = sa.Column(sa.String(1024), nullable=False)
    date_created = sa.Column(sa.DateTime, default=datetime.utcnow)
    date_updated = sa.Column(sa.DateTime, onupdate=datetime.utcnow)

    @declared_attr
    def text_column(cls):
        return synonym("title")

    @declared_attr
    def book_id(cls):
        return sa.Column(sa.Integer, sa.ForeignKey("book.id"), nullable=False)

    @declared_attr
    def book(cls):
        reverse_name = f"{cls.__name__.lower()}s"
        return relationship("Book", foreign_keys=[cls.book_id], backref=reverse_name)


class Bookmark(AnnotationBase):
    """Represents a user-defined bookmark."""
    __tablename__ = "bookmark"


class TaggedContent(AnnotationBase, TaggedMixin):
    __abstract__ = True
    __tablename__ = "tagged_content"

    @declared_attr
    def content(cls):
        return deferred(sa.Column(sa.Text, nullable=False))

    @declared_attr
    def text_column(cls):
        return synonym("content")


class Note(TaggedContent):
    """Represents user comments (notes)."""
    __tablename__ = "note"
    # Like Quote, a note can have a start and an end position
    # difference is that they are allowed to be None, and if so, it means they are targeting the whole line
    start_pos = sa.Column(sa.Integer, default = None)
    end_pos = sa.Column(sa.Integer, default = None)
    

class Quote(TaggedContent):
    """Represents a highlight (quote) from the book."""
    __tablename__ = "quote"

    start_pos = sa.Column(sa.Integer, nullable=False)
    end_pos = sa.Column(sa.Integer, nullable=False)
