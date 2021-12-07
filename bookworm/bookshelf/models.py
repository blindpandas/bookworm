# coding: utf-8

import os
import attr
import ujson
from datetime import datetime
from peewee import *
from playhouse.sqlite_ext import (
    FTS5Model,
    AutoIncrementField,
    RowIDField,
    JSONField,
    SearchField,
)
from bookworm.paths import db_path
from .database import (
    AutoOptimizedAPSWDatabase,
    AutoCalculatedField,
    BooleanField,
    DateTimeField,
    DocumentUriField,
    ImageField,
    SqliteViewSchemaManager,
)


BOOKWORM_BOOKSHELF_APP_ID = 10194273
BOOKWORM_BOOKSHELF_SCHEMA_VERSION = 1
DEFAULT_BOOKSHELF_DATABASE_FILE = db_path("bookshelf.sqlite")
database = AutoOptimizedAPSWDatabase(
    os.fspath(DEFAULT_BOOKSHELF_DATABASE_FILE),
    json_contains=True,
    pragmas=[
        ("cache_size", -1024 * 64),
        ("journal_mode", "wal"),
        ("foreign_keys", 1),
    ],
)
TRIGGER_DELETE_FTS_INDEX_ON_PAGE_DELETE = (
    "CREATE TRIGGER IF NOT EXISTS doc_fts_idx_remove AFTER DELETE ON page\n"
    "BEGIN\n"
    "INSERT INTO document_fts_index(document_fts_index, rowid, page_number, document_id, content)\n"
    "VALUES('delete', old.id, old.number, old.document_id, old.content);\n"
    "END;"
)


@attr.s(auto_attribs=True, slots=True, frozen=True)
class FullTextSearchResult:
    document_id: int
    page_index: int
    document_title: str = None
    snippet: str = None

    @property
    def document(self):
        return Document.get_by_id(self.document_id)
        doc_id = VwDocumentPage.get(page_id=1).document_id
        return Document.get_by_id(doc_id)


class BaseModel(Model):
    class Meta:
        database = database
        legacy_table_names = False

    @classmethod
    def create_all(cls):
        database = cls._meta.database
        database.create_tables(
            (
                Author,
                Category,
                Format,
                Tag,
                Document,
                Page,
                VwDocumentPage,
                DocumentAuthor,
                DocumentTag,
                DocumentFTSIndex,
            )
        )
        with database:
            cursor = database.connection().cursor()
            cursor.execute(f"PRAGMA application_id={BOOKWORM_BOOKSHELF_APP_ID}")
            cursor.execute(f"PRAGMA user_version={BOOKWORM_BOOKSHELF_SCHEMA_VERSION}")
            # Create a trigger to remove FTS indexes for deleted pages
            cursor.execute(TRIGGER_DELETE_FTS_INDEX_ON_PAGE_DELETE)


class Author(BaseModel):
    name = TextField(index=True, null=False)


class Category(BaseModel):
    name = TextField(unique=True, null=False)


class Format(BaseModel):
    name = CharField(max_length=64, unique=True, null=False)


class Tag(BaseModel):
    name = TextField(unique=True, null=False)


class Document(BaseModel):
    id = AutoIncrementField()
    uri = DocumentUriField(unique=True, null=False)
    title = TextField(index=True, null=False)
    publication_date = DateTimeField(index=True, null=True)
    date_added = DateTimeField(default=datetime.utcnow, index=True, null=False)
    cover_image = ImageField(null=True)
    format = ForeignKeyField(
        column_name="format_id",
        field="id",
        model=Format,
        backref="documents",
    )
    category = ForeignKeyField(
        column_name="category_id",
        field="id",
        model=Category,
        backref="documents",
    )
    metadata = JSONField(json_dumps=ujson.dumps, json_loads=ujson.loads, null=True)


class Page(BaseModel):
    number = IntegerField(null=False)
    content = TextField(null=False)
    document = ForeignKeyField(
        column_name="document_id",
        field="id",
        model=Document,
        backref="pages",
        on_delete="CASCADE"
    )


class DocumentAuthor(BaseModel):
    document = ForeignKeyField(
        column_name="document_id", field="id", model=Document, backref="authors"
    )
    author = ForeignKeyField(
        column_name="author_id", field="id", model=Author, backref="documents"
    )

    class Meta:
        indexes = ((("document", "author"), True),)
        primary_key = CompositeKey("document", "author")


class DocumentTag(BaseModel):
    document = ForeignKeyField(
        column_name="document_id", field="id", model=Document, backref="tags"
    )
    tag = ForeignKeyField(
        column_name="tag_id", field="id", model=Tag, backref="documents"
    )

    class Meta:
        indexes = ((("document", "tag"), True),)
        primary_key = CompositeKey("document", "tag")


class VwDocumentPage(BaseModel):
    """A custom view to aggregate information from the document and page tables."""

    page_id = IntegerField()
    page_number = IntegerField()
    document_id = IntegerField()
    document_title = TextField()
    content = TextField()

    @classmethod
    def view_select_builder(cls):
        return Page.select(
            Page.id.alias("page_id"),
            Page.number.alias("page_number"),
            Document.id.alias("document_id"),
            Document.title.alias("document_title"),
            Page.content.alias("content"),
        ).join(Document, on=Page.document_id == Document.id)

    class Meta:
        primary_key = False
        schema_manager_class = SqliteViewSchemaManager


class DocumentFTSIndex(BaseModel, FTS5Model):
    rowid = RowIDField()
    page_number = SearchField(unindexed=True)
    document_id = SearchField(unindexed=True)
    document_title = SearchField(unindexed=True)
    content = SearchField()

    @classmethod
    def add_document_to_search_index(cls, document_id):
        return DocumentFTSIndex.insert_from(
            (
                VwDocumentPage.select(
                    VwDocumentPage.page_id.alias("rowid"),
                    VwDocumentPage.page_number.alias("page_number"),
                    VwDocumentPage.document_id.alias("document_id"),
                    VwDocumentPage.document_title.alias("document_title"),
                    VwDocumentPage.content.alias("content"),
                )
                .join(Document, on=VwDocumentPage.document_id == Document.id)
                .join(Page, on=VwDocumentPage.page_id == Page.id)
                .where(Document.id == document_id)
            ),
            fields=[
                "rowid",
                "page_number",
                "document_id",
                "document_title",
                "content",
            ],
        )

    @classmethod
    def perform_search(cls, column, term):
        if not cls.validate_query(term):
            term = cls.clean_query(term)
        return (
            cls.select(
                cls.page_number,
                cls.document_id,
                cls.document_title,
                column.snippet(left="", right="", over_length="", max_tokens=24),
            )
            .where(column.match(term))
            .order_by(fn.bm25(cls._meta.entity))
            .order_by(cls.document_id)
            .order_by(cls.page_number.asc())
        )

    @classmethod
    def search_for_term(cls, term) -> list[FullTextSearchResult]:
        connection = cls._meta.database.connection()
        with connection:
            cursor = connection.cursor()
            content_matches = cursor.execute(str(cls.perform_search(cls.content, term)))
            for (page_number, document_id, document_title, snippet) in content_matches:
                yield FullTextSearchResult(
                    page_index=page_number,
                    document_id=document_id,
                    document_title=document_title,
                    snippet=snippet,
                )

    @classmethod
    def optimize(cls):
        return cls._fts_cmd('optimize')

    class Meta:
        extension_module = "fts5"
        options = {
            "tokenize": "porter unicode61",
            "content": VwDocumentPage,
            "content_rowid": VwDocumentPage.page_id,
        }
