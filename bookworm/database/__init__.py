# coding: utf-8

"""
Persistent stoarage using SQLlite3
"""

import os
import sqlite3

import db_magic as db
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from bookworm.logger import logger
from bookworm.paths import db_path as get_db_path

from .models import (
    Book,
    Base,
    DocumentPositionInfo,
    GetOrCreateMixin,
    PinnedDocument,
    RecentDocument,
)
from .schema import upgrade_database_schema

log = logger.getChild(__name__)

def get_db_url() -> str:
    db_path = os.path.join(get_db_path(), "database.sqlite")
    return f"sqlite:///{db_path}"

def init_database():
    engine = create_engine(get_db_url())
    Base.metadata.create_all(engine)
    Base.session = scoped_session(
        sessionmaker(engine, autocommit=False, autoflush=False)
    )

