# coding: utf-8

"""
Database models for `Bookworm`.
"""

from . import db


class GetOrCreateMixin:
    """Adds the `get_or_create` method to a sqlalchemy Model class."""

    @classmethod
    def get_or_create(cls, **kwargs):
        obj = cls.query.filter_by(**kwargs).one_or_none()
        if obj is not None:
            return obj
        return cls(**kwargs)


class Book(db.Model):
    identifier = db.string(512, unique=True, nullable=False)
    title = db.string(512, nullable=False)
    file_path = db.string(1024, nullable=False)
