"""create table area models

Revision ID: 96712cf64e86
Revises: fac39899d2a4
Create Date: 2025-05-05 19:32:10.497693

"""
from typing import Sequence, Union

from src.alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96712cf64e86'
down_revision: Union[str, None] = 'fac39899d2a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('area',
                    sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
                    sa.Column('quantity', sa.Float(), nullable=False),
                    sa.Column('serial_number', sa.String(20), nullable=True),
                    sa.Column('material_id', sa.String(20), nullable=True),
                    sa.Column('provide_type', sa.String(20), nullable=False),
                    sa.Column('card_number', sa.String(10), nullable=False),
                    sa.Column('username', sa.String(50), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
                    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
                    sa.Column('stock_id', sa.Integer(), sa.ForeignKey('stock.id', ondelete='CASCADE')),
                    sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE')),
                    sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id', ondelete='CASCADE'))

                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('area')
