# coding: utf-8

import typing
from peewee import *
from peewee import NodeList, EnclosedNodeList, ColumnBase
from playhouse.apsw_ext import APSWDatabase, BooleanField, DateTimeField
from bookworm.document.uri import DocumentUri
from bookworm.image_io import ImageIO


class AutoOptimizedAPSWDatabase(APSWDatabase):
    """Optimizes the database after closing each connection as per recommended practices for sqlite3."""

    def close(self):
        cursor = self.connection().cursor()
        cursor.execute("PRAGMA optimize")
        super().close()


class AutoCalculatedField(Field):

    AUTO_GEN_COLUMN_TYPES = (
        "virtual",
        "stored",
    )

    def __init__(
        self,
        *args,
        auto_gen_data_type: typing.Union[Field, str],
        auto_gen_expression: ColumnBase,
        auto_gen_always: bool = True,
        auto_gen_column_type: str = "virtual",
        **kwargs,
    ):
        assert (
            auto_gen_column_type in self.AUTO_GEN_COLUMN_TYPES
        ), f"auto_gen_column_type must be one of {self.AUTO_GEN_COLUMN_TYPES}"
        super().__init__(*args, **kwargs)
        self.auto_gen_data_type = auto_gen_data_type
        self.auto_gen_expression = auto_gen_expression
        self.auto_gen_always = auto_gen_always
        self.auto_gen_column_type = auto_gen_column_type

    def ddl_datatype(self, ctx):
        return (
            self.auto_gen_data_type
            if type(self.auto_gen_data_type) is str
            else self.auto_gen_data_type().ddl_datatype(ctx)
        )

    def ddl(self, ctx):
        node_list = super().ddl(ctx)
        ag_auto_gen = SQL("GENERATED ALWAYS" if self.auto_gen_always else "")
        ag_col_type = SQL(self.auto_gen_column_type.upper())
        return NodeList(
            (
                node_list,
                ag_auto_gen,
                SQL("AS"),
                EnclosedNodeList(
                    [
                        self.auto_gen_expression,
                    ]
                ),
                ag_col_type,
            )
        )


class ImageField(BlobField):
    """Uses ImageIO to store and retreive images from the database."""

    def db_value(self, value):
        return value.as_bytes(format="JPEG")

    def python_value(self, value):
        return ImageIO.from_bytes(value)


class DocumentUriField(TextField):
    def db_value(self, value):
        return value.to_uri_string()

    def python_value(self, value):
        return DocumentUri.from_uri_string(value)


class SqliteViewSchemaManager(SchemaManager):
    def _create_table(self, safe=True, **options):
        if not getattr(self.model, "view_select_builder", None):
            raise TypeError("view_select_builder method is required on view tables.")
        meta = self.model._meta
        columns = {field.column_name for field in meta.sorted_fields}
        is_temp = options.pop("temporary", False)
        ctx = self._create_context()
        ctx.literal("CREATE TEMPORARY VIEW " if is_temp else "CREATE VIEW ")
        if safe:
            ctx.literal("IF NOT EXISTS ")
        ctx.sql(self.model).literal(" ")
        ctx.literal("AS ")
        ctx.sql(self.model.view_select_builder())
        return ctx
