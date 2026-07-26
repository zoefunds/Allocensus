"""Make stake_wei a bigint

Revision ID: 003_stake_wei_bigint
Revises: 002_add_rebalancing_metadata
Create Date: 2026-07-26 10:59:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_stake_wei_bigint"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "rebalancing_proposals",
        "stake_wei",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "rebalancing_proposals",
        "stake_wei",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
