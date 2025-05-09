"""add column warehouse model doc_num

Revision ID: 45decc2f672a
Revises: 96712cf64e86
Create Date: 2025-05-08 13:48:50.217200

"""
from typing import Sequence, Union

from src.alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45decc2f672a'
down_revision: Union[str, None] = '96712cf64e86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('warehouse', sa.Column('doc_num', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('warehouse', 'doc_num')
