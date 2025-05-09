"""create table users, projects

Revision ID: 69bdd24824e9
Revises: 
Create Date: 2025-04-16 15:54:17.283446

"""
from typing import Sequence, Union

from src.alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69bdd24824e9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('projects',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('project_name', sa.String(40), nullable=False),
        sa.Column('project_code', sa.String(20), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('first_name', sa.String(40), nullable=False),
        sa.Column('middle_name', sa.String(40), nullable=True),
        sa.Column('last_name', sa.String(40), nullable=False),
        sa.Column('email', sa.String(40), nullable=False, unique=True),
        sa.Column('password', sa.String(100), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, default=False),
        sa.Column('profile_image', sa.String(255), nullable=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index(op.f('ix_users_id'), 'users', ['id'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'])

    projects_table = sa.table('projects',
                              sa.column('id', sa.Integer()),
                              sa.column('project_name', sa.String()),
                              sa.column('project_code', sa.String()),
                              sa.column('created_at', sa.DateTime())
                              )


    op.bulk_insert(projects_table, [{'project_name':"Head", 'project_code':"Head"}])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')

    op.drop_table('users')
    op.drop_table('projects')