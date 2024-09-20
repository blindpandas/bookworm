# coding: utf-8

"""
Database models for Annotations.
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred, relationship, synonym

from bookworm.database import GetOrCreateMixin, Base


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


class Quote(TaggedContent):
    """Represents a highlight (quote) from the book."""
    __tablename__ = "quote"

    start_pos = sa.Column(sa.Integer, nullable=False)
    end_pos = sa.Column(sa.Integer, nullable=False)
