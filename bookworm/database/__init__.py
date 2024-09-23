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
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from bookworm import app
from bookworm.logger import logger
from bookworm import paths
from bookworm.paths import db_path as get_db_path

from .models import (
    Book,
    Base,
    DocumentPositionInfo,
    GetOrCreateMixin,
    PinnedDocument,
    RecentDocument,
)

log = logger.getChild(__name__)

def get_db_url() -> str:
    db_path = os.path.join(get_db_path(), "database.sqlite")
    return f"sqlite:///{db_path}"

def init_database():
    engine = create_engine(get_db_url())
    log.info("Running database migrations and setup")
    cfg_file = None
    script_location = "alembic"
    if app.is_frozen:
        cfg_file = sys._MEIPASS
        script_location = paths.app_path("alembic")
    else:
        cfg_file = Path(__file__).parent.parent
    
    cfg = Config(Path(cfg_file, "alembic.ini"))
    cfg.set_main_option('script_location', str(script_location))
    command.upgrade(cfg, "head")
    Base.session = scoped_session(
        sessionmaker(engine, autocommit=False, autoflush=False)
    )

