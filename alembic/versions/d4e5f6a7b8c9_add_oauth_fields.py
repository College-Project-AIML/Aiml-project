"""add_oauth_fields

Revision ID: d4e5f6a7b8c9
Revises: acb7ea47699f
Create Date: 2026-09-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'acb7ea47699f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add OAuth columns and make password_hash nullable for OAuth users."""
    op.add_column('users', sa.Column('oauth_provider', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('oauth_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))

    # Make password_hash nullable — OAuth users won't have one
    op.alter_column('users', 'password_hash', nullable=True)

    # Add indexes for OAuth lookups
    op.create_index('ix_users_oauth', 'users', ['oauth_provider', 'oauth_id'])


def downgrade() -> None:
    """Remove OAuth columns and restore password_hash NOT NULL."""
    op.drop_index('ix_users_oauth', table_name='users')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')
    op.alter_column('users', 'password_hash', nullable=False)
