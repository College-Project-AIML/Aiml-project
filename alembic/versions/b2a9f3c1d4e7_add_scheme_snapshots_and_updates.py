"""add scheme snapshots and updates tables

Revision ID: b2a9f3c1d4e7
Revises: acb7ea47699f
Create Date: 2026-08-06 12:00:00.000000

Adds the change-detection bookkeeping tables for the live-sync pipeline
(docs/next.md §2.1):

    scheme_snapshots — what a scheme looked like the last time we fetched it
    scheme_updates   — one row per detected change (the "what's new" feed)

Note: ``scheme_snapshots.snapshot`` stores the semantic fields as JSON so the
pipeline can emit precise ``changed_fields`` diffs, while ``fingerprint`` is
the sha256 over those fields.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "b2a9f3c1d4e7"
down_revision: Union[str, Sequence[str], None] = "acb7ea47699f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the change-detection tables."""
    op.create_table(
        "scheme_snapshots",
        sa.Column(
            "scheme_id",
            UUID(as_uuid=True),
            sa.ForeignKey("schemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column("snapshot", JSONB(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("miss_count", sa.Integer(), server_default="0", nullable=False),
        # Connector key (e.g. "myscheme") — scopes CLOSED detection so a run
        # for one source never marks another source's schemes as missing.
        sa.Column("source", sa.String(255), nullable=False),
    )

    op.create_table(
        "scheme_updates",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "scheme_id",
            UUID(as_uuid=True),
            sa.ForeignKey("schemes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("change_type", sa.String(20), nullable=False),
        sa.Column("changed_fields", JSONB(), nullable=True),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_index("idx_scheme_updates_detected", "scheme_updates", ["detected_at"])
    op.create_index("idx_scheme_updates_scheme", "scheme_updates", ["scheme_id"])


def downgrade() -> None:
    """Drop the change-detection tables."""
    op.drop_index("idx_scheme_updates_scheme", table_name="scheme_updates")
    op.drop_index("idx_scheme_updates_detected", table_name="scheme_updates")
    op.drop_table("scheme_updates")
    op.drop_table("scheme_snapshots")
