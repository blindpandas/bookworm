# coding: utf-8

"""
Contains database schema upgrade rutines for bookworm 
"""

from contextlib import suppress
import sqlalchemy as sa
from db_magic.schema_upgrades import perform_upgrade
import bookworm.typehints as t
from bookworm.logger import logger

log = logger.getChild(__name__)
CURRENT_SCHEMA_VERSION = 0


def get_upgrades() -> t.Dict[int, t.Tuple[t.Callable]]:
    return {}


def upgrade_database_schema(session):
    perform_upgrade(
        session, upgrades=get_upgrades(), schema_version=CURRENT_SCHEMA_VERSION
    )
