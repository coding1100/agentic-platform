"""add_user_state_and_api_usage

Revision ID: e1b7d2a4f7c1
Revises: 573fce6048e9
Create Date: 2026-02-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e1b7d2a4f7c1'
down_revision: Union[str, None] = '573fce6048e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add system flag to users
    op.add_column('users', sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.false()))

    # Add rate limiting window fields to api_keys
    op.add_column('api_keys', sa.Column('rate_limit_window_start', sa.DateTime(), nullable=True))
    op.add_column('api_keys', sa.Column('rate_limit_window_count', sa.Integer(), nullable=False, server_default='0'))

    # Create api_key_usage_daily table
    op.create_table(
        'api_key_usage_daily',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('api_key_id', 'usage_date', name='uq_api_key_usage_daily'),
    )
    op.create_index('ix_api_key_usage_daily_api_key_id', 'api_key_usage_daily', ['api_key_id'])

    # Create user_states table
    op.create_table(
        'user_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('namespace', sa.String(), nullable=False),
        sa.Column('data', postgresql.JSON, nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'namespace', name='uq_user_state_namespace'),
    )
    op.create_index('ix_user_states_user_id', 'user_states', ['user_id'])
    op.create_index('ix_user_states_namespace', 'user_states', ['namespace'])


def downgrade() -> None:
    op.drop_index('ix_user_states_namespace', table_name='user_states')
    op.drop_index('ix_user_states_user_id', table_name='user_states')
    op.drop_table('user_states')

    op.drop_index('ix_api_key_usage_daily_api_key_id', table_name='api_key_usage_daily')
    op.drop_table('api_key_usage_daily')

    op.drop_column('api_keys', 'rate_limit_window_count')
    op.drop_column('api_keys', 'rate_limit_window_start')
    op.drop_column('users', 'is_system')
