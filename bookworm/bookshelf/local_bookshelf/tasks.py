# coding: utf-8

import more_itertools
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
from bottle import request, abort
from bookworm import typehints as t
from bookworm.concurrency import threaded_worker
from bookworm.document import BaseDocument, create_document
from bookworm.document.uri import DocumentUri
from bookworm.document.elements import DocumentInfo
from bookworm.signals import app_shuttingdown, local_server_booting
from bookworm.logger import logger
from .models import (
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
ADD_TO_BOOKSHELF_URL_PREFIX = '/add-to-bookshelf'
IMPORT_FOLDER_TO_BOOKSHELF_URL_PREFIX = '/import-folder-to-bookshelf'
local_bookshelf_process_executor = ProcessPoolExecutor(max_workers=8)


@app_shuttingdown.connect
def _shutdown_local_bookshelf_process_executor(sender):
    local_bookshelf_process_executor.shutdown(wait=False)


@local_server_booting.connect
def _add_document_index_endpoint(sender):
    sender.route(ADD_TO_BOOKSHELF_URL_PREFIX, method='POST', callback=add_to_bookshelf_view)
    sender.route(IMPORT_FOLDER_TO_BOOKSHELF_URL_PREFIX, method='POST', callback=import_folder_to_bookshelf_view)


def add_document_to_bookshelf(
    document: BaseDocument,
    category_name: str,
    tags_names: list[str],
    database_file: t.PathLike
):
    """Add the given document to the bookshelf database."""
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
    cover_image = document.get_cover_image()
    metadata = document.metadata
    format, __ = Format.get_or_create(name=document.uri.format)
    if category_name:
        category, __ = Category.get_or_create(name=category_name)
    else:
        category = None
    log.debug("Adding document to the database ")
    doc_info_dict = DocumentInfo.from_document(document).asdict(excluded_fields=('cover_image',))
    doc = Document.create(
        uri=document.uri,
        title=metadata.title,
        cover_image=cover_image,
        format=format,
        category=category,
        metadata=doc_info_dict
    )
    doc.save()
    doc_id = doc.get_id()
    if (author_name := metadata.author):
        author, __ = Author.get_or_create(name=author_name)
        DocumentAuthor.create(
            document_id=doc_id,
            author_id=author.get_id()
        )
    if type(tags_names) is str:
        tags_names = [t.strip() for t in tags_names.split(" ")]
    tags = [Tag.get_or_create(name=t)[0] for t in tags_names]
    for tag in tags:
        DocumentTag.create(
            document_id=doc_id,
            tag_id=tag.get_id()
        )
    fields = [Page.number, Page.content, Page.document]
    page_objs = ((page.index, page.get_text(), doc) for page in document)
    for batch in more_itertools.chunked(page_objs, 100):
        Page.insert_many(batch, fields).execute()
    DocumentFTSIndex.add_document_to_search_index(doc.get_id()).execute()
    DocumentFTSIndex.optimize()


def add_to_bookshelf_view():
    data = request.json
    doc_uri = data['document_uri']
    try:
        document = create_document(DocumentUri.from_uri_string(doc_uri))
    except:
        log.exception(f"Failed to open document: {doc_uri}", exc_info=True)
        abort(400, f'Failed to open document: {doc_uri}')
    else:
        if document.__internal__:
            abort(400, f'Document is an internal document: {doc_uri}')
        else:
            local_bookshelf_process_executor.submit(
                add_document_to_bookshelf,
                document,
                data['category'],
                data['tags'],
                data['database_file']
            )
            return {'status': 'OK', 'document_uri': doc_uri}


def import_folder_to_bookshelf_view():
    data = request.json
    folder = Path(data['folder'])
    if (not folder.is_dir()) or (not folder.exists()):
        return {'status': 'Failed', 'reason': 'Folder not found'}
    category_name = data.get('category_name') or folder.name
    threaded_worker.submit(
        _do_import_folder_to_bookshelf,
        folder,
        category_name
    )
    return {'satus': 'processing'}


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
    with ThreadPoolExecutor(max_workers=8, thread_name_prefix="bookshelf.import.folder") as executor:
        for retval in executor.map(partial(_import_document, category_name), doc_filenames):
            if retval:
                log.info(f"Added document: {retval}")


def _import_document(category_name, filename):
    try:
        uri = DocumentUri.from_filename(filename)
        document = create_document(uri)
    except:
        return
    add_document_to_bookshelf(document, category_name, tags_names=(), database_file=None)
    document.close()
