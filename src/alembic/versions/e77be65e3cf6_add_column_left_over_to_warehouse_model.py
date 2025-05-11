"""Add Column left_over to warehouse model

Revision ID: e77be65e3cf6
Revises: 9f4109b3d625
Create Date: 2025-05-02 11:53:01.427890

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e77be65e3cf6'
down_revision: Union[str, None] = '9f4109b3d625'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('warehouse', sa.Column('left_over', sa.Float()))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('warehouse', 'left_over')
