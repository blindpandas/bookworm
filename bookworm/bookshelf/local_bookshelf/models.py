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
from bookworm.document import DocumentInfo
from bookworm.i18n import LocaleInfo
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
    page_id: int
    page_index: int
    document_title: str = None
    snippet: str = None

    @property
    def document(self):
        return Document.get_by_id(self.document_id)


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

    @classmethod
    def get_all(cls):
        return (
            Author.select()
            .join(DocumentAuthor, on=DocumentAuthor.author_id)
            .where(DocumentAuthor.author_id == Author.id)
            .distinct()
            .order_by(Author.name)
        )

    @classmethod
    def get_documents(cls, name):
        return (
            Document.select()
            .join(DocumentAuthor, on=DocumentAuthor.document_id == Document.id)
            .join(Author, on=DocumentAuthor.author_id == Author.id)
            .where(Author.name == name)
        )
        

class Category(BaseModel):
    name = TextField(unique=True, null=False)

    @classmethod
    def get_all(cls):
        return Category.select().distinct().order_by(Category.name)

    @classmethod
    def get_documents(cls, name):
        return (
            Document.select()
            .join(Category)
            .where(Category.name == name)
        )


class Format(BaseModel):
    name = CharField(max_length=64, unique=True, null=False)


class Tag(BaseModel):
    name = TextField(unique=True, null=False)

    @classmethod
    def get_all(cls):
        return Tag.select().distinct().order_by(Tag.name)

    @classmethod
    def get_documents(cls, name):
        return (
            Document.select()
            .join(DocumentTag, on=DocumentTag.document_id == Document.id)
            .join(Tag, on=DocumentTag.tag_id == Tag.id)
            .where(Tag.name == name)
        )


class Document(BaseModel):
    id = AutoIncrementField()
    uri = DocumentUriField(unique=True, null=False)
    title = TextField(index=True, null=False)
    date_added = DateTimeField(default=datetime.utcnow, index=True, null=False)
    is_favorite = BooleanField(default=False)
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
        null=True,
    )
    metadata = JSONField(json_dumps=ujson.dumps, json_loads=ujson.loads, null=True, default={})

    def as_document_info(self) -> DocumentInfo:
        kwargs = self.metadata.copy()
        kwargs['uri'] = self.uri
        kwargs['cover_image'] = self.cover_image
        kwargs['language'] = LocaleInfo(kwargs['language'])
        kwargs.setdefault('data', {}).update(database_id=self.get_id())
        return DocumentInfo(**kwargs)

    def change_category_and_tags(self, category_name=None, tags_names=()) -> bool:
        is_category_created = is_tag_created = False
        if category_name is not None:
            if category_name:
                categ, is_category_created = Category.get_or_create(name=category_name)
                self.category =categ
            else:
                self.category = None
        if tags_names is not None:
            DocumentTag.delete().where(DocumentTag.document_id == self.get_id()).execute()
            for tag_name in (t.strip() for t in tags_names if t.strip()):
                tag, is_tag_created = Tag.get_or_create(name=tag_name)
                DocumentTag.create(
                    document_id=self.get_id(),
                    tag_id=tag.get_id()
                )
        self.save()
        return any([is_category_created, is_tag_created])


class Page(BaseModel):
    number = IntegerField(null=False)
    content = TextField(null=False)
    document = ForeignKeyField(
        column_name="document_id",
        field="id",
        model=Document,
        backref="pages",
        on_delete="CASCADE",
    )

    @classmethod
    def get_text_start_position(cls, page_id, text):
        return (
            cls.select(fn.ABS(fn.INSTR(cls.content, text)))
            .where(cls.id == page_id)
        ).scalar()


class DocumentAuthor(BaseModel):
    document = ForeignKeyField(
        column_name="document_id",
        field="id",
        model=Document,
        backref="authors",
        on_delete="CASCADE"
    )
    author = ForeignKeyField(
        column_name="author_id",
        field="id",
        model=Author,
        backref="documents",
        on_delete="CASCADE"
    )

    class Meta:
        indexes = ((("document", "author"), True),)
        primary_key = CompositeKey("document", "author")


class DocumentTag(BaseModel):
    document = ForeignKeyField(
        column_name="document_id",
        field="id",
        model=Document,
        backref="tags",
        on_delete="CASCADE"
    )
    tag = ForeignKeyField(
        column_name="tag_id",
        field="id",
        model=Tag,
        backref="documents",
        on_delete="CASCADE"
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
    document_title = SearchField()
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
                cls.rowid,
                cls.page_number,
                cls.document_id,
                cls.document_title,
                column.snippet(left="", right="", over_length="", max_tokens=20),
            )
            .where(column.match(term))
            .order_by(fn.bm25(cls._meta.entity))
        )

    @classmethod
    def search_for_term(cls, term, field='content') -> list[FullTextSearchResult]:
        assert field in ('title', 'content'), "Field should be one of: (title, content)"
        field_column = (
            cls.document_title
            if field == 'title'
            else cls.content
        )
        connection = cls._meta.database.connection()
        with connection:
            cursor = connection.cursor()
            content_matches = cursor.execute(str(cls.perform_search(field_column, term)))
            yielded_docs = set()
            for (page_id, page_number, document_id, document_title, snippet) in content_matches:
                if document_id in yielded_docs:
                    continue
                if field == 'title':
                    yielded_docs.add(document_id)
                yield FullTextSearchResult(
                    page_id=page_id,
                    page_index=page_number,
                    document_id=document_id,
                    document_title=document_title,
                    snippet=snippet,
                )

    @classmethod
    def optimize(cls):
        return cls._fts_cmd("optimize")

    class Meta:
        extension_module = "fts5"
        options = {
            "tokenize": "porter unicode61",
            "content": VwDocumentPage,
            "content_rowid": VwDocumentPage.page_id,
        }
