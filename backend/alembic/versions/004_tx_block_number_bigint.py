"""Make tx_block_number a bigint

Revision ID: 004_tx_block_number_bigint
Revises: 003_stake_wei_bigint
Create Date: 2026-07-26 11:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "004_tx_block_number_bigint"
down_revision = "003_stake_wei_bigint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "rebalancing_proposals",
        "tx_block_number",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "rebalancing_proposals",
        "tx_block_number",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
