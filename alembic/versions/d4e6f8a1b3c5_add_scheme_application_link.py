"""add an optional direct application link to schemes

Revision ID: d4e6f8a1b3c5
Revises: c3f8a1b2d5e9
Create Date: 2026-09-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e6f8a1b3c5"
down_revision: Union[str, Sequence[str], None] = "c3f8a1b2d5e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("schemes", sa.Column("application_link", sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column("schemes", "application_link")
