# coding: utf-8

"""
Persistent storage using SQLlite3
"""
import os
from pathlib import Path
import sqlite3
import sys

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from bookworm import app
from bookworm.logger import logger
from bookworm import paths
from bookworm.paths import db_path as get_db_path

from .models import *

log = logger.getChild(__name__)


def get_db_url() -> str:
    db_path = os.path.join(get_db_path(), "database.sqlite")
    return f"sqlite:///{db_path}"


def init_database(engine=None, url: str = None, **kwargs) -> bool:
    if not url:
        url = get_db_url()
    if engine == None:
        engine = create_engine(url, **kwargs)
    log.debug(f"Using url {url} ")
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        rev = context.get_current_revision()
        # let's check for the book table
        # Should it be too ambiguous, we'd have to revisit what tables should be checked to determine whether the DB is at the baseline point
        cursor = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        tables = [row[0] for row in cursor.fetchall()]
        is_baseline = tables != None and "book" in tables and rev == None
    log.info(f"Current revision is {rev}")
    log.info("Running database migrations and setup")
    cfg_file = ""
    script_location = "alembic"
    if app.is_frozen:
        cfg_file = sys._MEIPASS
        script_location = paths.app_path("alembic")

    cfg = Config(Path(cfg_file, "alembic.ini"))
    # we set this attribute in order to prevent alembic from configuring logging if we're running the commands programmatically.
    # This is because otherwise our loggers would be overridden
    cfg.attributes["configure_logger"] = False
    cfg.set_main_option("script_location", str(script_location))
    cfg.set_main_option("sqlalchemy.url", url)
    if rev == None:
        if is_baseline:
            log.info(
                "No revision was found, but the database appears to be at the baseline required to begin tracking."
            )
            log.info("Stamping alembic revision")
            command.stamp(cfg, "28099038d8d6")
    command.upgrade(cfg, "head")
    Base.session = scoped_session(
        sessionmaker(engine, autocommit=False, autoflush=False)
    )
    return engine
