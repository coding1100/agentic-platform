"""set_flash_as_default_agent_model

Revision ID: e3f1a2b4c6d8
Revises: d2a4c5f6e7b8
Create Date: 2026-04-27 00:10:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "e3f1a2b4c6d8"
down_revision = "d2a4c5f6e7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE agents
        SET model = 'gemini-2.5-flash'
        WHERE model IN ('gemini-1.5-pro', 'gemini-2.5-pro')
        """
    )
    op.execute(
        """
        ALTER TABLE agents
        ALTER COLUMN model SET DEFAULT 'gemini-2.5-flash'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE agents
        ALTER COLUMN model SET DEFAULT 'gemini-2.5-pro'
        """
    )
