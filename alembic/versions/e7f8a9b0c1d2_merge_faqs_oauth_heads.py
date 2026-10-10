"""Merge the FAQs and OAuth migration branches.

Revision ID: e7f8a9b0c1d2
Revises: c3f8a1b2d5e9, d4e5f6a7b8c9
Create Date: 2026-10-10

"""
from typing import Sequence, Union


# Revision identifiers, used by Alembic.
revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = ("c3f8a1b2d5e9", "d4e5f6a7b8c9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
