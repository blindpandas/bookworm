"""add_text_model_version_columns

Revision ID: b743b2dbd3a1
Revises: 707543f03b6d
Create Date: 2026-05-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b743b2dbd3a1"
down_revision: str | None = "707543f03b6d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in (
        "book",
        "document_position_info",
        "recent_document",
        "pinned_document",
    ):
        op.add_column(
            table_name,
            sa.Column("content_hash_version", sa.Integer(), nullable=True),
        )

    op.add_column(
        "document_position_info",
        sa.Column("position_version", sa.Integer(), nullable=True),
    )
    for table_name in ("bookmark", "note", "quote"):
        op.add_column(
            table_name,
            sa.Column("position_version", sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    for table_name in ("quote", "note", "bookmark"):
        op.drop_column(table_name, "position_version")
    op.drop_column("document_position_info", "position_version")

    for table_name in (
        "pinned_document",
        "recent_document",
        "document_position_info",
        "book",
    ):
        op.drop_column(table_name, "content_hash_version")
