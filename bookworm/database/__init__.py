# coding: utf-8

"""
Database models for `Bookworm`.
"""

import sqlite3
import os
import db_magic as db
from bookworm import config
from bookworm.paths import home_data_path, db_path as get_db_path
from bookworm.logger import logger
from .models import *


log = logger.getChild(__name__)

FILE_HISTORY_DB_PATH = home_data_path("file_history.db")


def init_database():
    db_path = os.path.join(get_db_path(), "db.sqlite")
    if not os.path.isfile(FILE_HISTORY_DB_PATH):
        create_file_history_db()
    return db.Model.setup_database(f"sqlite:///{db_path}", create=True)


def create_file_history_db():
    sql = """
        CREATE TABLE file_history
        (id INTEGER PRIMARY KEY, file_path TEXT, last_page INTEGER, last_pos INTEGER)
    """
    con = sqlite3.connect(FILE_HISTORY_DB_PATH)
    con.execute(sql)


def get_last_position(file_path):
    if not config.conf["general"]["open_with_last_position"]:
        return
    sql = "SELECT last_page, last_pos FROM file_history WHERE file_path=?"
    try:
        con = sqlite3.connect(FILE_HISTORY_DB_PATH)
        retval = con.execute(sql, (file_path,)).fetchone()
        con.close()
        return retval
    except sqlite3.Error as e:
        log.exception(f"Sqlite error, {e.args}.")


def save_last_position(file_path, last_page, last_pos):
    if get_last_position(file_path) is not None:
        sql = "UPDATE file_history SET last_page=?, last_pos=? WHERE file_path=?"
        values = (last_page, last_pos, file_path)
    else:
        sql = (
            "INSERT INTO file_history (file_path, last_page, last_pos) VALUES (?, ?, ?)"
        )
        values = (file_path, last_page, last_pos)
    try:
        con = sqlite3.connect(FILE_HISTORY_DB_PATH)
        with con:
            con.execute(sql, values)
        con.close()
    except sqlite3.Error as e:
        log.exception(f"Sqlite error, {e.args}.")
