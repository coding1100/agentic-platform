"""Add prebuilt agent fields

Revision ID: 002_add_prebuilt_agent_fields
Revises: 001_initial
Create Date: 2026-01-06 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_add_prebuilt_agent_fields"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
  op.add_column(
    "agents",
    sa.Column("slug", sa.String(), nullable=True),
  )
  op.add_column(
    "agents",
    sa.Column("category", sa.String(), nullable=True),
  )
  op.add_column(
    "agents",
    sa.Column("is_prebuilt", sa.Boolean(), nullable=False, server_default=sa.false()),
  )
  op.add_column(
    "agents",
    sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
  )
  op.create_unique_constraint("uq_agents_slug", "agents", ["slug"])


def downgrade() -> None:
  op.drop_constraint("uq_agents_slug", "agents", type_="unique")
  op.drop_column("agents", "is_active")
  op.drop_column("agents", "is_prebuilt")
  op.drop_column("agents", "category")
  op.drop_column("agents", "slug")


