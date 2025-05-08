"""create table group, ordered, companies, warehouse, category, material_codes

Revision ID: 9f4109b3d625
Revises: ad78fd5d046b
Create Date: 2025-04-23 06:01:59.894965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f4109b3d625'
down_revision: Union[str, None] = 'ad78fd5d046b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table('companies',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('company_name',sa.String(255), nullable=False),
                    sa.Column('country',sa.String(40), nullable=True),
                    sa.Column('email',sa.String(40), nullable=True),
                    sa.Column('phone_number',sa.String(40), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=False,server_default=sa.func.now()),
                    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
                    )

    op.create_table('groups',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('group_name', sa.String(30), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False,server_default=sa.func.now())
                    )

    op.create_table('ordered',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('f_name', sa.String(30), nullable=False),
                    sa.Column('m_name', sa.String(30), nullable=True),
                    sa.Column('l_name', sa.String(30), nullable=False),
                    sa.Column('email', sa.String(30), nullable=False),
                    sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id')),
                    sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id')),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
                    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
                    )

    op.create_table('categories',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('category_name', sa.String(100), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False,server_default=sa.func.now()),
                    )

    op.create_table('material_codes',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('code_num', sa.String(10), nullable=False),
                    sa.Column('description', sa.String(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False,server_default=sa.func.now()),
                    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
                    )

    op.create_table('warehouse',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('material_name', sa.Text(), nullable=False),
                    sa.Column('qty', sa.Float(), nullable=False),
                    sa.Column('unit', sa.String(20), nullable=False),
                    sa.Column('price', sa.Float(), nullable=True),
                    sa.Column('currency', sa.String(20), nullable=True),
                    sa.Column('po_num', sa.String(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False,server_default=sa.func.now()),

                    sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE')),
                    sa.Column('material_code_id', sa.Integer(), sa.ForeignKey('material_codes.id', ondelete='CASCADE')),
                    sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='CASCADE')),
                    sa.Column('ordered_id', sa.Integer(), sa.ForeignKey('ordered.id', ondelete='CASCADE')),
                    sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE')),
                    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),

                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('warehouse')
    op.drop_table('companies')
    op.drop_table('ordered')
    op.drop_table('groups')
    op.drop_table('categories')
    op.drop_table('material_codes')
