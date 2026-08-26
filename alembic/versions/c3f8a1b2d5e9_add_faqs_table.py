"""add faqs table for chatbot

Revision ID: c3f8a1b2d5e9
Revises: b2a9f3c1d4e7
Create Date: 2026-08-25 22:00:00.000000

Adds the `faqs` table used by the AI-powered FAQ chatbot.

    faqs — one row per FAQ entry; links to a scheme via scheme_id (nullable FK).
          The question text is what gets embedded for semantic search.

Note: schemas/postgres.sql has also been updated with this DDL so that
      fresh Docker containers receive the table via the init script.
      Existing databases that already ran alembic should run:
          alembic upgrade head
      There is no drift risk for fresh containers because ``CREATE TABLE IF
      NOT EXISTS`` is idempotent; stamping head after ``docker compose up``
      keeps the Alembic version table in sync.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "c3f8a1b2d5e9"
down_revision: Union[str, Sequence[str], None] = "b2a9f3c1d4e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the faqs table."""
    op.create_table(
        "faqs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "scheme_id",
            UUID(as_uuid=True),
            sa.ForeignKey("schemes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("idx_faqs_scheme_id", "faqs", ["scheme_id"])


def downgrade() -> None:
    """Drop the faqs table."""
    op.drop_index("idx_faqs_scheme_id", table_name="faqs")
    op.drop_table("faqs")
