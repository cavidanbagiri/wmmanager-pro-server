"""create table stock models

Revision ID: fac39899d2a4
Revises: e77be65e3cf6
Create Date: 2025-05-02 16:19:51.463738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fac39899d2a4'
down_revision: Union[str, None] = 'e77be65e3cf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table("stock",
                    sa.Column('id',sa.Integer(), autoincrement=True, primary_key=True),
                    sa.Column('quantity', sa.Float(), nullable=False),
                    sa.Column('left_over', sa.Float(), nullable=False),
                    sa.Column('serial_number', sa.String(length=20), nullable=True),
                    sa.Column('material_id', sa.String(length=20), nullable=True),
                    sa.Column('created_at', sa.DateTime(),server_default=sa.func.now() ),
                    sa.Column('warehouse_id', sa.Integer, sa.ForeignKey("warehouse.id")),
                    sa.Column('created_by_id', sa.Integer, sa.ForeignKey("users.id")),
                    sa.Column('project_id', sa.Integer, sa.ForeignKey("projects.id")),
                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('stock')

