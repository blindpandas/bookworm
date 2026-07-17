"""allow multiple book records per uri

Revision ID: c7f4e1a2b9d6
Revises: b743b2dbd3a1
Create Date: 2026-07-17 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7f4e1a2b9d6"
down_revision: str | None = "b743b2dbd3a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    index_name = op.f("ix_book_uri")
    op.drop_index(index_name, table_name="book")
    op.create_index(index_name, "book", ["uri"], unique=False)


def downgrade() -> None:
    index_name = op.f("ix_book_uri")
    op.drop_index(index_name, table_name="book")
    op.create_index(index_name, "book", ["uri"], unique=True)
