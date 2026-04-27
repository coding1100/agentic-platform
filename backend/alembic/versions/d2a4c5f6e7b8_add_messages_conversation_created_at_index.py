"""add_messages_conversation_created_at_index

Revision ID: d2a4c5f6e7b8
Revises: b7f9c2d4e8a1
Create Date: 2026-04-27 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "d2a4c5f6e7b8"
down_revision = "b7f9c2d4e8a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_messages_conversation_created_at
        ON messages (conversation_id, created_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_messages_conversation_created_at")
