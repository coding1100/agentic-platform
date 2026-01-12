"""make_api_key_agent_id_nullable

Revision ID: 9c28622cb26e
Revises: 003_api_keys
Create Date: 2026-01-12 18:43:33.169036

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9c28622cb26e'
down_revision: Union[str, None] = '003_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make agent_id nullable to support universal API keys (keys that work for all agents)
    op.alter_column('api_keys', 'agent_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True)


def downgrade() -> None:
    # Revert agent_id to not nullable
    # Note: This will fail if there are any NULL values in agent_id
    op.alter_column('api_keys', 'agent_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)
