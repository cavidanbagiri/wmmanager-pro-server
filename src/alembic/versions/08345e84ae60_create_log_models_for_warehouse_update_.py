"""Create Log models for warehouse_update, stock and area return

Revision ID: 08345e84ae60
Revises: 45decc2f672a
Create Date: 2025-05-11 11:07:06.951162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08345e84ae60'
down_revision: Union[str, None] = '45decc2f672a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('log_stock_movement',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
                    sa.Column('movement_type', sa.String(), nullable=False),
                    sa.Column('old_quantity', sa.Float(), nullable=False),
                    sa.Column('old_left_over', sa.Float(), nullable=False),
                    sa.Column('return_quantity', sa.Float(), nullable=False),
                    sa.Column('new_left_over', sa.Float(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
                    sa.Column('stock_id', sa.Integer(), sa.ForeignKey('stock.id', ondelete='CASCADE')),
                    sa.Column('warehouse_id', sa.Integer(), sa.ForeignKey('warehouse.id', ondelete='CASCADE')),
                    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'))
                    )

    op.create_table('log_area_movement',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
                    sa.Column('movement_type', sa.String(), nullable=False),
                    sa.Column('old_quantity', sa.Float(), nullable=False),
                    sa.Column('return_quantity', sa.Float(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
                    sa.Column('area_id', sa.Integer(), sa.ForeignKey('area.id', ondelete='CASCADE')),
                    sa.Column('stock_id', sa.Integer(), sa.ForeignKey('stock.id', ondelete='CASCADE')),
                    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'))
                    )

    op.create_table('log_warehouse_movement',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
                    sa.Column('movement_type', sa.String(), nullable=False),
                    sa.Column('old_quantity', sa.Float(), nullable=False),
                    sa.Column('old_left_over', sa.Float(), nullable=False),
                    sa.Column('new_quantity', sa.Float(), nullable=False),
                    sa.Column('new_left_over', sa.Float(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
                    sa.Column('warehouse_id', sa.Integer(), sa.ForeignKey('warehouse.id', ondelete='CASCADE')),
                    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'))
                    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('log_stock_movement')
    op.drop_table('log_area_movement')
    op.drop_table('log_warehouse_movement')
