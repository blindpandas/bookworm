# coding: utf-8

"""
Contains database schema upgrade rutines for bookworm 
"""

from contextlib import suppress
from datetime import datetime
import sqlalchemy as sa
from db_magic.schema_upgrades import perform_upgrade
import bookworm.typehints as t
from bookworm.logger import logger

log = logger.getChild(__name__)
CURRENT_SCHEMA_VERSION = 1


def get_upgrades() -> t.Dict[int, t.Tuple[t.Callable]]:
    return {
        1: (v1_schema_upgrade,),
    }


def upgrade_database_schema(session):
    perform_upgrade(
        session, upgrades=get_upgrades(), schema_version=CURRENT_SCHEMA_VERSION
    )


def v1_schema_upgrade(session, connection):
    """Upgrade to schema version 1, effective since Bookworm v0.2b1."""
    sql = []
    # Added a 'file_path' field to the 'book' table
    sql.append(
        "ALTER TABLE book ADD COLUMN file_path VARCHAR(1024) NOT NULL DEFAULT ''"
    )
    # Added date created and date updated to 'note' and 'bookmark' tables
    new_cols = ("date_created DATETIME", "date_updated DATETIME")
    tables_to_change = ("note", "bookmark")
    for table in tables_to_change:
        for col in new_cols:
            sql.append(f"ALTER TABLE {table} ADD COLUMN {col}")
    for stmt in sql:
        with suppress(sa.exc.OperationalError):
            session.execute(stmt)
