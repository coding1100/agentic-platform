"""add_allowed_origins_to_api_keys

Revision ID: 573fce6048e9
Revises: 9c28622cb26e
Create Date: 2026-01-12 18:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '573fce6048e9'
down_revision: Union[str, None] = '9c28622cb26e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add allowed_origins JSON column to api_keys table
    # null or empty list = allow all origins
    op.add_column('api_keys', 
        sa.Column('allowed_origins', postgresql.JSON, nullable=True)
    )


def downgrade() -> None:
    # Remove allowed_origins column
    op.drop_column('api_keys', 'allowed_origins')
