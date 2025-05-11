"""create table tokens

Revision ID: 3a7a7af561e3
Revises: 69bdd24824e9
Create Date: 2025-04-20 11:02:58.116084

"""
from typing import Sequence, Union

from alembic import op

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3a7a7af561e3'
down_revision: Union[str, None] = '69bdd24824e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('tokens',
                    sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
                    sa.Column('tokens', sa.String()),
                    sa.Column('user_id', sa.Integer(),sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('tokens')
