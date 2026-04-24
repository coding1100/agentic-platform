"""archive_and_remove_realtime_livekit

Revision ID: b7f9c2d4e8a1
Revises: a9d92f7de3c4
Create Date: 2026-04-24 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7f9c2d4e8a1"
down_revision: Union[str, None] = "a9d92f7de3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Archive realtime tables before removal.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS archived_agent_embed_deployments
        AS TABLE agent_embed_deployments WITH NO DATA
        """
    )
    op.execute(
        """
        INSERT INTO archived_agent_embed_deployments
        SELECT * FROM agent_embed_deployments
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS archived_realtime_sessions
        AS TABLE realtime_sessions WITH NO DATA
        """
    )
    op.execute(
        """
        INSERT INTO archived_realtime_sessions
        SELECT * FROM realtime_sessions
        """
    )

    # Drop realtime tables and agent realtime columns.
    op.execute("DROP TABLE IF EXISTS realtime_sessions")
    op.execute("DROP TABLE IF EXISTS agent_embed_deployments")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS realtime_config")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS avatar_id")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS avatar_provider")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS livekit_agent_name")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS interaction_mode")


def downgrade() -> None:
    # Re-introducing realtime/livekit schema is intentionally unsupported.
    raise RuntimeError("Downgrade is not supported for realtime/livekit hard removal.")
