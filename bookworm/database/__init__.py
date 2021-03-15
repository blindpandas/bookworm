# coding: utf-8

"""
Persistent stoarage using SQLlite3
"""

import sqlite3
import os
import db_magic as db
from bookworm.paths import home_data_path, db_path as get_db_path
from bookworm.logger import logger
from .models import (
    GetOrCreateMixin,
    Book,
    RecentDocument,
    PinnedDocument,
    DocumentPositionInfo,
)
from .schema import upgrade_database_schema

log = logger.getChild(__name__)


def init_database():
    db_path = os.path.join(get_db_path(), "db.sqlite")
    db.Model.setup_database(f"sqlite:///{db_path}", create=True)
    upgrade_database_schema(db.Model.session)
