# coding: utf-8

"""
Database models for Annotations.
"""

import sqlalchemy as sa
from sqlalchemy.orm import synonym, relationship, deferred
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from bookworm.database import db
from bookworm.database import GetOrCreateMixin


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
            db.Model.metadata,
            sa.Column(f"{remote1}_id", sa.Integer, sa.ForeignKey(f"{remote1}.id")),
            sa.Column(f"{remote2}_id", sa.Integer, sa.ForeignKey(f"{remote2}.id")),
        )

    @declared_attr
    def tags(cls):
        if not hasattr(cls, "Tag"):
            # Create the Tag model
            tag_attrs = {
                "id": sa.Column(sa.Integer, primary_key=True),
                "title": db.string(512, nullable=False, unique=True, index=True),
                "items": relationship(
                    cls,
                    secondary=lambda: cls.__tags_association_table__,
                    backref="related_tags",
                ),
            }
            cls.Tag = type(
                f"{cls.__name__}Tag", (GetOrCreateMixin, db.Model), tag_attrs
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


class AnnotationBase(db.Model):
    __abstract__ = True
    title = db.string(255, nullable=False)
    page_number = db.integer(nullable=False)
    position = db.integer(nullable=False, default=0)
    section_title = db.string(1024, nullable=False)
    section_identifier = db.string(1024, nullable=False)
    date_created = sa.Column(sa.DateTime, default=datetime.now)
    date_updated = sa.Column(sa.DateTime, onupdate=datetime.now)

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


class TaggedContent(AnnotationBase, TaggedMixin):
    __abstract__ = True

    @declared_attr
    def content(cls):
        return deferred(db.text(nullable=False))

    @declared_attr
    def text_column(cls):
        return synonym("content")


class Note(TaggedContent):
    """Represents user comments (notes)."""


class Quote(TaggedContent):
    """Represents a highlight (quote) from the book."""

    start_pos = db.integer(nullable=False)
    end_pos = db.integer(nullable=False)
