"""QRead interoperability"""

import sqlite3
from typing import Optional

from pydantic import BaseModel, ValidationError

from bookworm.logger import logger

log = logger.getChild(__name__)


class BookInfo(BaseModel):
    """Saved book information
    QRead stores book metadata inside a .qrd file, which is an unencrypted sqlite database
    The table we are interested from is named shelf, and it contains information related to book position, among other things
    """

    # Current position of the book
    current_position: int
    # File location of the book
    original_path: str


def get_book_info(qrd_path: str) -> Optional[BookInfo]:
    """Connects to the .qrd sqlite database and retrieves the book information we require, if any"""
    log.debug(f"Connecting to {qrd_path}")
    with sqlite3.connect(qrd_path) as conn:
        cur = conn.cursor()
        # the shelf table is made up by two columns, key and value
        cur.execute('SELECT value FROM shelf WHERE key="book.json"')
        try:
            value = cur.fetchone()[0]
            info = BookInfo.model_validate_json(value)
            return info
        except ValidationError:
            log.error("Failed to obtain book information from QRD file", exc_info=True)
            return None
        finally:
            cur.close()
