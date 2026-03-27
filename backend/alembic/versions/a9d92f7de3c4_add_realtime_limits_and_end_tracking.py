"""add_realtime_limits_and_end_tracking

Revision ID: a9d92f7de3c4
Revises: f4a6c1d9b7e3
Create Date: 2026-02-23 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a9d92f7de3c4"
down_revision: Union[str, None] = "f4a6c1d9b7e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agent_embed_deployments",
        sa.Column("max_concurrent_sessions", sa.Integer(), nullable=False, server_default="5"),
    )
    op.add_column("realtime_sessions", sa.Column("ended_at", sa.DateTime(), nullable=True))
    op.create_index("ix_realtime_sessions_ended_at", "realtime_sessions", ["ended_at"])


def downgrade() -> None:
    op.drop_index("ix_realtime_sessions_ended_at", table_name="realtime_sessions")
    op.drop_column("realtime_sessions", "ended_at")
    op.drop_column("agent_embed_deployments", "max_concurrent_sessions")
