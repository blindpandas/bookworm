# coding: utf-8

from __future__ import annotations
import os
import atexit
import threading
import mimetypes
import urllib.parse
import zipfile
from tempfile import TemporaryDirectory
from functools import lru_cache, cached_property
from bottle import (
    Bottle,
    Router,
    HTTPError,
    template,
    request,
    response,
    static_file,
    abort,
)
from bookworm import typehints as t
from bookworm import paths
from bookworm.utils import generate_sha1hash
from bookworm.concurrency import threaded_worker
from bookworm.logger import logger


log = logger.getChild(__name__)

WEB_RESOURCES_PATH = paths.resources_path("readium_js_viewer_lite")
TEMPLATE_PATH = WEB_RESOURCES_PATH / "templates"
OPENED_EPUBS: dict[str, tuple[ZipFile, list[str]]] = {}


class EpubServingConfig:
    def __init__(self, app):
        self.app = app
        atexit.register(self.close)
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
    def get_template(self, filename):
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
                threaded_worker.submit(
                    self.extract_epub,
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
            return {"deleted": book_uid}

    def index_view(self):
        if (book_path := request.query.get("epub")) is None or book_path.strip(
            " /"
        ).split("/")[-1] not in OPENED_EPUBS:
            raise HTTPError(400, "Missing or Invalid book_uid")
        response.status = "200 OK"
        return TEMPLATE_PATH.joinpath("index.html").read_bytes()

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
