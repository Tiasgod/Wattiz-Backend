"""initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('hashed_password', sa.String(length=256), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ── appliances ────────────────────────────────────────────────────────────
    op.create_table(
        'appliances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('power_watts', sa.Float(), nullable=False),
        sa.Column('hours_per_day', sa.Float(), nullable=False),
        sa.Column('days_per_month', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('category', sa.String(length=60), nullable=False, server_default='Outros'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_appliances_user_id', 'appliances', ['user_id'])

    # ── tariffs ───────────────────────────────────────────────────────────────
    op.create_table(
        'tariffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('distributor', sa.String(length=120), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=True),
        sa.Column('kwh_price', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tariffs_user_id', 'tariffs', ['user_id'])

    # ── consumption_records ───────────────────────────────────────────────────
    op.create_table(
        'consumption_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appliance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_month', sa.Integer(), nullable=False),
        sa.Column('reference_year', sa.Integer(), nullable=False),
        sa.Column('kwh_consumed', sa.Float(), nullable=False),
        sa.Column('estimated_cost', sa.Float(), nullable=False),
        sa.Column('tariff_used', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['appliance_id'], ['appliances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_consumption_records_user_id', 'consumption_records', ['user_id'])
    op.create_index('ix_consumption_records_appliance_id', 'consumption_records', ['appliance_id'])

    # ── reports ───────────────────────────────────────────────────────────────
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_month', sa.Integer(), nullable=False),
        sa.Column('reference_year', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default='{}'),
        sa.Column('lume_summary', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reports_user_id', 'reports', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_reports_user_id', table_name='reports')
    op.drop_table('reports')

    op.drop_index('ix_consumption_records_appliance_id', table_name='consumption_records')
    op.drop_index('ix_consumption_records_user_id', table_name='consumption_records')
    op.drop_table('consumption_records')

    op.drop_index('ix_tariffs_user_id', table_name='tariffs')
    op.drop_table('tariffs')

    op.drop_index('ix_appliances_user_id', table_name='appliances')
    op.drop_table('appliances')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
