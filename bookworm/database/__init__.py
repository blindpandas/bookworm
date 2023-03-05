# coding: utf-8

"""
Persistent stoarage using SQLlite3
"""

import os
import sqlite3

import db_magic as db

from bookworm.logger import logger
from bookworm.paths import db_path as get_db_path

from .models import (Book, DocumentPositionInfo, GetOrCreateMixin,
                     PinnedDocument, RecentDocument)
from .schema import upgrade_database_schema

log = logger.getChild(__name__)


def init_database():
    db_path = os.path.join(get_db_path(), "database.sqlite")
    db.Model.setup_database(f"sqlite:///{db_path}", create=True)
    upgrade_database_schema(db.Model.session)
