# coding: utf-8

"""
Database models for `Bookworm`.
"""

import sqlalchemy as sa
from sqlalchemy.orm import deferred
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy
from . import db


class AnnotationBase(db.Model):
    __abstract__ = True
    title = db.string(255, nullable=False)
    page_number = db.integer(nullable=False)
    position = db.integer()
    section_title = db.string(1024, nullable=False)
    section_identifier = db.string(1024, nullable=False)


class Bookmark(AnnotationBase):
    """Represents a user-defined bookmark."""


class Note(AnnotationBase):
    """Represents user notes."""

    content = deferred(db.text())


class Quote(AnnotationBase):
    """Represents a quote from the book."""
    content = deferred(db.text())
    start_pos = db.integer(nullable=False)
    end_pos = db.integer(nullable=False)


class Book(db.Model):
    identifier = db.string(512, unique=True, nullable=False)
    title = db.string(512, nullable=False)
    bookmarks = db.one_to_many(
        "Bookmark", "book_id", relationship_kw={"backref": "book", "lazy": "dynamic"}
    )
    notes = db.one_to_many(
        "Note", "book_id", relationship_kw={"backref": "book", "lazy": "dynamic"}
    )
    quotes = db.one_to_many(
        "Quote", "book_id", relationship_kw={"backref": "book", "lazy": "dynamic"}
    )
