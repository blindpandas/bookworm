"""Fix annotation position offset due to initial newline

Revision ID: 52e39c4f7494
Revises: 35f453946f1e
Create Date: 2025-07-14 20:04:27.707924

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import bookworm

# revision identifiers, used by Alembic.
revision: str = "52e39c4f7494"
down_revision: Union[str, None] = "35f453946f1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Subtracts 1 from all position-related columns in annotation and document position tables.
    This corrects the +1 offset from old data, aligning it with the new "clean" index logic.
    """
    print("Applying data migration to fix all known position offsets...")

    # --- Fix Last Reading Position ---
    op.execute(
        "UPDATE document_position_info SET last_position = last_position - 1 WHERE last_position > 0;"
    )

    # --- Fix Bookmark positions ---
    op.execute("UPDATE bookmark SET position = position - 1;")

    # --- Fix Quote positions ---
    op.execute("UPDATE quote SET start_pos = start_pos - 1, end_pos = end_pos - 1;")

    # --- Fix Note positions (Robust multi-step update) ---
    op.execute("UPDATE note SET position = position - 1;")
    op.execute("UPDATE note SET start_pos = start_pos - 1 WHERE start_pos IS NOT NULL;")
    op.execute("UPDATE note SET end_pos = end_pos - 1 WHERE end_pos IS NOT NULL;")

    print("All position offset corrections applied.")


def downgrade() -> None:
    """
    Adds 1 back to all position-related columns to revert the data to its original offset state.
    """
    print("Reverting data migration for all position offsets...")

    # --- Revert Last Reading Position ---
    op.execute("UPDATE document_position_info SET last_position = last_position + 1;")

    # --- Revert Bookmark positions ---
    op.execute("UPDATE bookmark SET position = position + 1;")

    # --- Revert Quote positions ---
    op.execute("UPDATE quote SET start_pos = start_pos + 1, end_pos = end_pos + 1;")

    # --- Revert Note positions (Robust multi-step update) ---
    op.execute("UPDATE note SET position = position + 1;")
    op.execute("UPDATE note SET start_pos = start_pos + 1 WHERE start_pos IS NOT NULL;")
    op.execute("UPDATE note SET end_pos = end_pos + 1 WHERE end_pos IS NOT NULL;")

    print("All position offset corrections reverted.")
