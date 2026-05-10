"""add_users_table

Revision ID: acb7ea47699f
Revises: 
Create Date: 2026-04-25 15:24:59.295279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acb7ea47699f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import uuid

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
        sa.Column('user_id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('income', sa.Numeric(12, 2), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('caste', sa.String(50), nullable=True),
        sa.Column('education', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('role', sa.String(20), server_default='user'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
