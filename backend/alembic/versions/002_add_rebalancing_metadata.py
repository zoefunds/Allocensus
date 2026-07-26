"""Add rebalancing transaction metadata

Revision ID: 002
Revises: 001
Create Date: 2026-07-26 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rebalancing_proposals", sa.Column("tx_block_number", sa.Integer(), nullable=True))
    op.add_column("rebalancing_proposals", sa.Column("tx_timestamp", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rebalancing_proposals", sa.Column("proposal_version", sa.String(length=32), nullable=False, server_default="1.0.0"))
    op.add_column("rebalancing_proposals", sa.Column("tx_wallet_address", sa.String(length=64), nullable=True))
    op.add_column("rebalancing_proposals", sa.Column("tx_authenticated_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("rebalancing_proposals", sa.Column("stake_wei", sa.Integer(), nullable=True))
    op.add_column("rebalancing_proposals", sa.Column("stake_refund_claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("rebalancing_proposals", "stake_refund_claimed")
    op.drop_column("rebalancing_proposals", "stake_wei")
    op.drop_column("rebalancing_proposals", "tx_authenticated_user_id")
    op.drop_column("rebalancing_proposals", "tx_wallet_address")
    op.drop_column("rebalancing_proposals", "proposal_version")
    op.drop_column("rebalancing_proposals", "tx_timestamp")
    op.drop_column("rebalancing_proposals", "tx_block_number")
