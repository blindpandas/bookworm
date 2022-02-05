# coding: utf-8

import os
import contextlib
import urllib.parse
import shutil
import peewee
import requests
import more_itertools
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
from bottle import request, abort
from bookworm import typehints as t
from bookworm import paths
from bookworm import local_server
from bookworm.runtime import IS_RUNNING_PORTABLE
from bookworm.concurrency import threaded_worker
from bookworm.utils import generate_file_md5
from bookworm.document import BaseDocument, create_document
from bookworm.document.uri import DocumentUri
from bookworm.document.elements import DocumentInfo
from bookworm.signals import app_shuttingdown, local_server_booting
from bookworm.logger import logger
from .models import (
    DEFAULT_BOOKSHELF_DATABASE_FILE,
    Document,
    Page,
    Category,
    Format,
    Author,
    Tag,
    DocumentFTSIndex,
    DocumentAuthor,
    DocumentTag,
)


log = logger.getChild(__name__)
ADD_TO_BOOKSHELF_URL_PREFIX = "/add-to-bookshelf"
IMPORT_FOLDER_TO_BOOKSHELF_URL_PREFIX = "/import-folder-to-bookshelf"
local_bookshelf_process_executor = ProcessPoolExecutor(max_workers=8)


@app_shuttingdown.connect
def _shutdown_local_bookshelf_process_executor(sender):
    local_bookshelf_process_executor.shutdown(wait=False)


@local_server_booting.connect
def _add_document_index_endpoint(sender):
    sender.route(
        ADD_TO_BOOKSHELF_URL_PREFIX, method="POST", callback=add_to_bookshelf_view
    )
    sender.route(
        IMPORT_FOLDER_TO_BOOKSHELF_URL_PREFIX,
        method="POST",
        callback=import_folder_to_bookshelf_view,
    )


def issue_add_document_request(
    document_uri,
    category_name=None,
    tags_names=(),
    database_file=DEFAULT_BOOKSHELF_DATABASE_FILE,
):
    url = urllib.parse.urljoin(
        local_server.get_local_server_netloc(), ADD_TO_BOOKSHELF_URL_PREFIX
    )
    data = {
        "document_uri": document_uri.to_uri_string(),
        "category": category_name,
        "tags": tags_names,
        "database_file": database_file,
    }
    res = requests.post(url, json=data)
    log.debug(f"Add document to local bookshelf response: {res}, {res.text}")


def issue_import_folder_request(folder, category_name):
    url = urllib.parse.urljoin(
        local_server.get_local_server_netloc(), IMPORT_FOLDER_TO_BOOKSHELF_URL_PREFIX
    )
    res = requests.post(url, json={"folder": folder, "category_name": category_name})
    log.debug(f"Add folder to bookshelf response: {res}")


def get_bundled_documents_folder():
    bd_path = paths.data_path("bundled_documents")
    if not bd_path.exists():
        bd_path.mkdir(parents=True, exist_ok=True)
    return bd_path


def copy_document_to_bundled_documents(source_document_path, bundled_documents_folder):
    if os.path.normpath(os.path.dirname(source_document_path)) == os.path.normpath(
        bundled_documents_folder
    ):
        return source_document_path
    src_md5 = generate_file_md5(source_document_path)
    bundled_document_path = os.path.join(
        bundled_documents_folder, src_md5 + os.path.splitext(source_document_path)[-1]
    )
    if os.path.isfile(bundled_document_path):
        return bundled_document_path
    try:
        shutil.copy(os.fspath(source_document_path), os.fspath(bundled_document_path))
    except:
        return
    return bundled_document_path


def add_document_to_bookshelf(
    document_or_uri: t.Union[BaseDocument, DocumentUri],
    category_name: str,
    tags_names: list[str],
    database_file: t.PathLike,
):
    """Add the given document to the bookshelf database."""
    document = (
        create_document(document_or_uri)
        if isinstance(document_or_uri, DocumentUri)
        else document_or_uri
    )
    if (existing_doc := Document.get_or_none(uri=document.uri)) is not None:
        log.debug("Document already in the database. Checking index...")
        db_page_count = (
            DocumentFTSIndex.select()
            .where(DocumentFTSIndex.document_id == existing_doc.get_id())
            .count()
        )
        if db_page_count == len(document):
            log.debug("Document index is OK")
            return
        else:
            log.debug("Document index is not well formed. Rebuilding index...")
            existing_doc.delete_instance()
    if IS_RUNNING_PORTABLE:
        bundled_document_path = copy_document_to_bundled_documents(
            source_document_path=document.get_file_system_path(),
            bundled_documents_folder=get_bundled_documents_folder(),
        )
        uri = document.uri.create_copy(path=bundled_document_path)
    else:
        uri = document.uri
    cover_image = document.get_cover_image()
    if cover_image:
        try:
            cover_image = cover_image.make_thumbnail(
                width=512,
                height=512,
                exact_fit=True,
            )
        except:
            cover_image = None
    metadata = document.metadata
    format, __ = Format.get_or_create(name=uri.format)
    if category_name:
        category, __ = Category.get_or_create(name=category_name)
    else:
        category = None
    log.debug("Adding document to the database ")
    doc_info_dict = DocumentInfo.from_document(document).asdict(
        excluded_fields=("cover_image",)
    )
    doc = Document.create(
        uri=uri,
        title=metadata.title,
        cover_image=cover_image,
        format=format,
        category=category,
        metadata=doc_info_dict,
    )
    doc.save()
    doc_id = doc.get_id()
    if author_name := metadata.author:
        author, __ = Author.get_or_create(name=author_name)
        DocumentAuthor.create(document_id=doc_id, author_id=author.get_id())
    if type(tags_names) is str:
        tags_names = [t.strip() for t in tags_names.split(" ")]
    tags = [
        Tag.get_or_create(name=t_name)[0] for t in tags_names if (t_name := t.strip())
    ]
    for tag in tags:
        DocumentTag.create(document_id=doc_id, tag_id=tag.get_id())
    fields = [Page.number, Page.content, Page.document]
    page_objs = ((page.index, page.get_text(), doc) for page in document)
    for batch in more_itertools.chunked(page_objs, 100):
        Page.insert_many(batch, fields).execute()
    DocumentFTSIndex.add_document_to_search_index(doc.get_id()).execute()
    DocumentFTSIndex.optimize()


def add_to_bookshelf_view():
    data = request.json
    doc_uri = data["document_uri"]
    try:
        document = create_document(DocumentUri.from_uri_string(doc_uri))
    except:
        log.exception(f"Failed to open document: {doc_uri}", exc_info=True)
        abort(400, f"Failed to open document: {doc_uri}")
    else:
        if document.__internal__:
            abort(400, f"Document is an internal document: {doc_uri}")
        else:
            local_bookshelf_process_executor.submit(
                add_document_to_bookshelf,
                document,
                data["category"],
                data["tags"],
                data["database_file"],
            )
            return {"status": "OK", "document_uri": doc_uri}


def import_folder_to_bookshelf_view():
    data = request.json
    folder = Path(data["folder"])
    if (not folder.is_dir()) or (not folder.exists()):
        return {"status": "Failed", "reason": "Folder not found"}
    category_name = data.get("category_name") or folder.name
    threaded_worker.submit(_do_import_folder_to_bookshelf, folder, category_name)
    return {"status": "processing"}


def _do_import_folder_to_bookshelf(folder, category_name):
    all_document_extensions = set()
    for doc_cls in BaseDocument.document_classes.values():
        if not doc_cls.__internal__:
            all_document_extensions.update(ext.strip("*") for ext in doc_cls.extensions)
    doc_filenames = (
        filename
        for filename in folder.iterdir()
        if (filename.is_file()) and (filename.suffix in all_document_extensions)
    )
    with ThreadPoolExecutor(
        max_workers=8, thread_name_prefix="bookshelf.import.folder"
    ) as executor:
        for retval in executor.map(
            partial(_import_document, category_name), doc_filenames
        ):
            if retval:
                log.info(f"Added document: {retval}")


def _import_document(category_name, filename):
    try:
        uri = DocumentUri.from_filename(filename)
        with contextlib.closing(create_document(uri)) as document:
            add_document_to_bookshelf(
                document,
                category_name,
                tags_names=(),
                database_file=DEFAULT_BOOKSHELF_DATABASE_FILE,
            )
    except:
        return


def bundle_single_document(database_file, doc_instance):
    bundled_documents_folder = get_bundled_documents_folder()
    document_src = doc_instance.uri.path
    if not os.path.isfile(document_src):
        return False, document_src, doc_instance.title
    copied_document_path = copy_document_to_bundled_documents(
        document_src, bundled_documents_folder
    )
    if not copied_document_path:
        return False, document_src, doc_instance.title
    doc_instance.uri = doc_instance.uri.create_copy(path=copied_document_path)
    try:
        doc_instance.save()
    except peewee.IntegrityError:
        return False, document_src, doc_instance.title
    return True, document_src, doc_instance.title
