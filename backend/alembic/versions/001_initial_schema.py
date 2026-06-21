"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table("users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin","portfolio_manager","analyst", name="userrole"), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_verification_token", sa.String(255), nullable=True),
        sa.Column("password_reset_token", sa.String(255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table("wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("address", sa.String(42), nullable=False, unique=True),
        sa.Column("derivation_path", sa.String(64), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_wallets_address", "wallets", ["address"])

    op.create_table("encrypted_keystores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("encrypted_private_key", sa.Text(), nullable=False),
        sa.Column("encrypted_mnemonic", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("investor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_tolerance", sa.Enum("conservative","moderate","aggressive","very_aggressive", name="risktolerance"), nullable=False),
        sa.Column("investment_horizon", sa.Enum("short","medium","long","very_long", name="investmenthorizon"), nullable=False),
        sa.Column("investment_objectives", postgresql.JSON(), nullable=False),
        sa.Column("liquidity_requirements", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("portfolios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("investor_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investor_profiles.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_value_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_rebalanced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("portfolio_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_class", sa.String(64), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("current_price_usd", sa.Float(), nullable=False),
        sa.Column("current_value_usd", sa.Float(), nullable=False),
        sa.Column("target_weight_pct", sa.Float(), nullable=False),
        sa.Column("current_weight_pct", sa.Float(), nullable=False),
        sa.Column("coingecko_id", sa.String(128), nullable=True),
        sa.Column("contract_address", sa.String(64), nullable=True),
        sa.Column("chain", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("portfolio_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total_value_usd", sa.Float(), nullable=False),
        sa.Column("allocations", postgresql.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("rebalancing_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.Enum("draft","submitted","pending_consensus","approved","rejected","failed", name="proposalstatus"), nullable=False, server_default="draft"),
        sa.Column("current_allocations", postgresql.JSON(), nullable=False),
        sa.Column("proposed_allocations", postgresql.JSON(), nullable=False),
        sa.Column("market_context", postgresql.JSON(), nullable=False),
        sa.Column("genlayer_tx_hash", sa.String(128), nullable=True),
        sa.Column("genlayer_tx_id", sa.String(128), nullable=True),
        sa.Column("constraint_violations", postgresql.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("rationale_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rebalancing_proposals.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("rationale_text", sa.Text(), nullable=False),
        sa.Column("risk_analysis", sa.Text(), nullable=True),
        sa.Column("constraint_analysis", sa.Text(), nullable=True),
        sa.Column("diversification_score", sa.Float(), nullable=True),
        sa.Column("liquidity_assessment", sa.Text(), nullable=True),
        sa.Column("objective_alignment", sa.Text(), nullable=True),
        sa.Column("validator_consensus", postgresql.JSON(), nullable=False),
        sa.Column("raw_contract_output", postgresql.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("validator_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rebalancing_proposals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("validator_address", sa.String(64), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("raw_output", postgresql.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.Enum(
            "user_login","user_logout","user_register","password_change","key_export",
            "portfolio_create","portfolio_update","portfolio_delete",
            "proposal_submit","proposal_approved","proposal_rejected",
            "report_export","admin_action", name="auditeventtype"
        ), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=True),
        sa.Column("resource_id", sa.String(128), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False),
        sa.Column("on_chain_ref", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("compliance_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("check_type", sa.String(64), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("details", postgresql.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table("report_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_type", sa.String(32), nullable=False),
        sa.Column("file_url", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in ["report_exports","compliance_logs","audit_events","validator_responses",
                  "rationale_results","rebalancing_proposals","portfolio_snapshots",
                  "portfolio_assets","portfolios","investor_profiles",
                  "encrypted_keystores","wallets","users"]:
        op.drop_table(table)
    for enum in ["userrole","risktolerance","investmenthorizon","proposalstatus","auditeventtype"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
