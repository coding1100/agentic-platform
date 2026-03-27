"""add_realtime_avatar_models

Revision ID: f4a6c1d9b7e3
Revises: e1b7d2a4f7c1
Create Date: 2026-02-23 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f4a6c1d9b7e3"
down_revision: Union[str, None] = "e1b7d2a4f7c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 1: extend agents for realtime/avatar configuration.
    op.add_column(
        "agents",
        sa.Column("interaction_mode", sa.String(), nullable=False, server_default="chat"),
    )
    op.add_column("agents", sa.Column("livekit_agent_name", sa.String(), nullable=True))
    op.add_column("agents", sa.Column("avatar_provider", sa.String(), nullable=True))
    op.add_column("agents", sa.Column("avatar_id", sa.String(), nullable=True))
    op.add_column("agents", sa.Column("realtime_config", postgresql.JSON(astext_type=sa.Text()), nullable=True))

    # Per-user embed deployment settings for customer-facing iframe integrations.
    op.create_table(
        "agent_embed_deployments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embed_id", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allowed_origins", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("token_ttl_seconds", sa.Integer(), nullable=False, server_default="900"),
        sa.Column("room_name_prefix", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "agent_id", name="uq_agent_embed_deployments_user_agent"),
        sa.UniqueConstraint("embed_id"),
    )
    op.create_index("ix_agent_embed_deployments_user_id", "agent_embed_deployments", ["user_id"])
    op.create_index("ix_agent_embed_deployments_agent_id", "agent_embed_deployments", ["agent_id"])
    op.create_index("ix_agent_embed_deployments_embed_id", "agent_embed_deployments", ["embed_id"])

    # Session-level bookkeeping for analytics, audit, and lifecycle tracking.
    op.create_table(
        "realtime_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embed_deployment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("room_name", sa.String(), nullable=False),
        sa.Column("participant_identity", sa.String(), nullable=False),
        sa.Column("participant_name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("session_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["embed_deployment_id"],
            ["agent_embed_deployments.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_realtime_sessions_user_id", "realtime_sessions", ["user_id"])
    op.create_index("ix_realtime_sessions_agent_id", "realtime_sessions", ["agent_id"])
    op.create_index("ix_realtime_sessions_embed_deployment_id", "realtime_sessions", ["embed_deployment_id"])
    op.create_index("ix_realtime_sessions_room_name", "realtime_sessions", ["room_name"])
    op.create_index("ix_realtime_sessions_participant_identity", "realtime_sessions", ["participant_identity"])
    op.create_index("ix_realtime_sessions_status", "realtime_sessions", ["status"])
    op.create_index("ix_realtime_sessions_expires_at", "realtime_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_realtime_sessions_expires_at", table_name="realtime_sessions")
    op.drop_index("ix_realtime_sessions_status", table_name="realtime_sessions")
    op.drop_index("ix_realtime_sessions_participant_identity", table_name="realtime_sessions")
    op.drop_index("ix_realtime_sessions_room_name", table_name="realtime_sessions")
    op.drop_index("ix_realtime_sessions_embed_deployment_id", table_name="realtime_sessions")
    op.drop_index("ix_realtime_sessions_agent_id", table_name="realtime_sessions")
    op.drop_index("ix_realtime_sessions_user_id", table_name="realtime_sessions")
    op.drop_table("realtime_sessions")

    op.drop_index("ix_agent_embed_deployments_embed_id", table_name="agent_embed_deployments")
    op.drop_index("ix_agent_embed_deployments_agent_id", table_name="agent_embed_deployments")
    op.drop_index("ix_agent_embed_deployments_user_id", table_name="agent_embed_deployments")
    op.drop_table("agent_embed_deployments")

    op.drop_column("agents", "realtime_config")
    op.drop_column("agents", "avatar_id")
    op.drop_column("agents", "avatar_provider")
    op.drop_column("agents", "livekit_agent_name")
    op.drop_column("agents", "interaction_mode")
