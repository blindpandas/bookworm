# coding: utf-8

from __future__ import annotations

import atexit
import mimetypes
import os
import threading
import urllib.parse
import zipfile
from functools import cached_property, lru_cache
from tempfile import TemporaryDirectory

import apsw
from bottle import (
    Bottle,
    HTTPError,
    abort,
    redirect,
    request,
    response,
    static_file,
    template,
)
from url_normalize import url_normalize

from bookworm import paths
from bookworm import typehints as t
from bookworm.concurrency import threaded_worker
from bookworm.logger import logger
from bookworm.utils import generate_sha1hash

log = logger.getChild(__name__)


EPUB_SERVE_APP_PREFIX = "/web_viewer/"
HISTORY_DB_PATH = paths.db_path("epub_server_history.sqlite")
WEB_RESOURCES_PATH = paths.resources_path("readium_js_viewer_lite")
TEMPLATE_PATH = WEB_RESOURCES_PATH / "templates"
OPENED_EPUBS: dict[str, TemporaryDirectory] = {}


class EpubServingConfig:
    def __init__(self, app):
        self.app = app
        atexit.register(self.close)
        self.db = apsw.Connection(os.fspath(HISTORY_DB_PATH))
        with self.db:
            cursor = self.db.cursor()
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS "history" '
                '("book_uid" varchar(128) NOT NULL, "url" text NOT NULL); '
                'CREATE UNIQUE INDEX IF NOT EXISTS "book_uid" ON "history" ("book_uid");'
            )
        self.app.resources.add_path(WEB_RESOURCES_PATH)
        self.add_epub_serving_routes()

    @property
    def default_routes(self):
        return {
            "/": (self.index_view, None),
            "/open_epub": (self.open_epub_view, dict(method="POST")),
            "/close_epub": (self.close_epub_view, dict(method="DELETE")),
            "/epubs/<book_uid>": (self.epub_archive_view, {"method": "HEAD"}),
            "/epubs/<book_uid>/<path:path>": (self.epub_archive_view, None),
        } | {
            f"/{folder}/<path:path>": (self.file_serving_view, None)
            for folder in (
                "css",
                "fonts",
                "font-faces",
                "images",
                "scripts",
            )
        }

    def add_epub_serving_routes(self):
        for (
            path,
            (
                view_func,
                view_kwargs,
            ),
        ) in self.default_routes.items():
            kwargs = view_kwargs or {}
            self.app.route(path, callback=view_func, **kwargs)

    @lru_cache()
    def get_template(self, filename, as_bytes=False):
        if as_bytes:
            return TEMPLATE_PATH.joinpath(filename).read_bytes()
        else:
            return TEMPLATE_PATH.joinpath(filename).read_text()

    def extract_epub(self, book_uid, filename):
        epub_extraction_dir = TemporaryDirectory()
        with zipfile.ZipFile(filename, "r") as archive:
            archive.extractall(path=epub_extraction_dir.name)
        OPENED_EPUBS[book_uid] = epub_extraction_dir

    def open_epub_view(self):
        if filename := request.json.get("filename"):
            if not os.path.isfile(filename):
                raise HTTPError(400, f"Bad epub file: {filename}")
            book_uid = generate_sha1hash(filename)
            if book_uid not in OPENED_EPUBS:
                self.extract_epub(
                    book_uid,
                    filename,
                )
            return {"book_uid": book_uid}
        raise HTTPError(400, f"Missing epub file name")

    def close_epub_view(self):
        book_uid = request.json.get("book_uid", "").strip()
        try:
            epub_temp_folder = OPENED_EPUBS[book_uid]
        except KeyError:
            raise HTTPError(404, f"Unown book uid {book_uid}")
        else:
            threading.Thread(target=epub_temp_folder.cleanup).start()
            OPENED_EPUBS.pop(book_uid)
            position_url = request.json.get("position_url", "").strip()
            position_url = urllib.parse.unquote(position_url)
            if position_url:
                with self.db:
                    cursor = self.db.cursor()
                    exists = cursor.execute(
                        'SELECT COUNT(*) FROM history WHERE "book_uid" = ?', (book_uid,)
                    ).fetchone()[0]
                    if not exists:
                        cursor.execute(
                            "INSERT INTO history values (?, ?)",
                            (book_uid, position_url),
                        )
                    else:
                        cursor.execute(
                            "UPDATE history SET position_url = ?", (position_url,)
                        )
            return {"deleted": book_uid}

    def index_view(self):
        book_uid = request.query.get("epub", "").strip(" /").split("/")[-1]
        if book_uid not in OPENED_EPUBS:
            response.status = "404 Not Found"
            return template(
                self.get_template("error.html"),
                title=_("404 Not Found"),
                message=_(
                    "The book you are trying to access does not exist or has been closed. "
                    "Please make sure you opened the book from within Bookworm. "
                    "All URLs are temporary and may not work after you close the page."
                ),
            )
        with self.db:
            cursor = self.db.cursor()
            result = cursor.execute(
                'SELECT (url) FROM history WHERE "book_uid" = ?', (book_uid,)
            ).fetchone()
            if result:
                position_url = result[0].lstrip("?")
                if position_url != request.query_string:
                    url_parts = request.urlparts
                    new_url = (
                        "{scheme}://{authority}/{path}/{EPUB_SERVE_APP_PREFIX}"
                        + "?{query}"
                    ).format(
                        scheme=url_parts.scheme,
                        authority=url_parts.netloc,
                        path="/",
                        EPUB_SERVE_APP_PREFIX=EPUB_SERVE_APP_PREFIX,
                        query=urllib.parse.unquote(position_url.lstrip("?")),
                    )
                    redirect(url_normalize(new_url))
        response.status = "200 OK"
        return self.get_template("index.html", as_bytes=True)

    def epub_archive_view(self, book_uid, path=None):
        if (request.path is None) or (request.method != "GET"):
            return HTTPError(301, "Moved Permanently")
        try:
            epub_extraction_dir = OPENED_EPUBS[book_uid]
        except KeyError:
            response.status = "400 Bad Request"
            return template(
                self.get_template("error.html"),
                dict(
                    title=_("Failed to load content"),
                    message=_(
                        "Cannot retreive content. Probably the eBook has been closed."
                    ),
                ),
            )
        filename = urllib.parse.unquote(path).strip("/")
        return static_file(filename, root=epub_extraction_dir.name)

    def file_serving_view(self, path):
        prefix = request.path.lstrip("/").split("/")[0].strip("/")
        return static_file(path, os.fspath(WEB_RESOURCES_PATH / prefix))

    def close(self):
        threading.Thread(
            target=self.cleanup_all,
        ).start()

    @staticmethod
    def cleanup_all():
        for tempfolder in OPENED_EPUBS.values():
            tempfolder.cleanup()


class EpubServingApp(Bottle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.epub_serving_config = EpubServingConfig(self)

    def close(self):
        super().close()
        self.epub_serving_config.close()
