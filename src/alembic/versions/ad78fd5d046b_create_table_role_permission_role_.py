"""create table role, permission, role_permission | add column role to user models 

Revision ID: ad78fd5d046b
Revises: 3a7a7af561e3
Create Date: 2025-04-21 15:34:45.569308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad78fd5d046b'
down_revision: Union[str, None] = '3a7a7af561e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('roles',
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
                    sa.Column('name', sa.String(20), unique=True),
                    sa.Column('description', sa.String(100)),
                    )

    op.create_table('permissions',
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
                    sa.Column('name', sa.String(20), unique=True))

    op.create_table('role_permissions',
                    sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id', ondelete='CASCADE'), ),
                    sa.Column('permission_id', sa.Integer(), sa.ForeignKey('permissions.id', ondelete='CASCADE')),
                    )

    op.add_column('users',
                  sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id', ondelete='CASCADE')))

    role_table = sa.table('roles',
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
                    sa.Column('name', sa.String(20), unique=True),
                    sa.Column('description', sa.String(100)),
                    )
    permission_table = sa.table('permissions',
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
                    sa.Column('name', sa.String(20), unique=True))

    role_permission = sa.table('role_permissions',
                    sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), ),
                    sa.Column('permission_id', sa.Integer(), sa.ForeignKey('permissions.id'),))

    op.bulk_insert(role_table,[
        {'name': 'Manager', 'description': 'All level access about all project warehouses'},
        {'name': 'Head', 'description': 'All level access about own warehouse'},
        {'name': 'Staff', 'description': 'Limited level access about own warehouse'},
        {'name': 'Operator', 'description': 'Create level access about own warehouse'},
        {'name': 'Guest', 'description': 'Read only access about own warehouse'},
    ])
    op.bulk_insert(permission_table,[
        {'name':'inventory:create'},
        {'name':'inventory:update'},
        {'name':'inventory:delete'},
        {'name':'inventory:view'},
    ])
    op.bulk_insert(role_permission,[
        {'role_id':1, 'permission_id': 1},
        {'role_id':1, 'permission_id': 2},
        {'role_id':1, 'permission_id': 3},
        {'role_id':1, 'permission_id': 4},
        {'role_id': 2, 'permission_id': 1},
        {'role_id': 2, 'permission_id': 2},
        {'role_id': 2, 'permission_id': 3},
        {'role_id': 2, 'permission_id': 4},
        {'role_id': 3, 'permission_id': 1},
        {'role_id': 3, 'permission_id': 2},
        {'role_id': 3, 'permission_id': 3},
        {'role_id': 4, 'permission_id': 1},
        {'role_id': 4, 'permission_id': 4},
        {'role_id': 5, 'permission_id': 4},
    ])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('role_permissions')
    op.drop_column('users', 'role_id')
    op.drop_table('roles')
    op.drop_table('permissions')
