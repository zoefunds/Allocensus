"""ALLOCENSUS — Initial migration + backend tests"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("backend/alembic/versions/001_initial_schema.py", '''\
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
''')

write("backend/tests/__init__.py", "")
write("backend/tests/unit/__init__.py", "")
write("backend/tests/integration/__init__.py", "")

write("backend/tests/conftest.py", '''\
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database import Base, get_db
from app.config import settings
import os

TEST_DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://allocensus_test:allocensus_test@localhost:5432/allocensus_test")

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db):
    async def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
''')

write("backend/tests/unit/test_constraints.py", '''\
import pytest
from app.utils.constraints import validate_portfolio_constraints


def test_valid_portfolio():
    allocations = {"BTC": 25.0, "ETH": 20.0, "USDC": 10.0, "AAPL": 20.0, "GOLD": 25.0}
    asset_classes = {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", "USDC": "stablecoins", "AAPL": "equities", "GOLD": "commodities"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    assert violations == [], f"Expected no violations but got: {violations}"


def test_single_asset_too_high():
    allocations = {"BTC": 35.0, "ETH": 15.0, "USDC": 10.0, "AAPL": 20.0, "GOLD": 20.0}
    asset_classes = {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", "USDC": "stablecoins", "AAPL": "equities", "GOLD": "commodities"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    rules = [v.rule for v in violations]
    assert "MAX_SINGLE_ASSET" in rules


def test_insufficient_liquidity():
    allocations = {"BTC": 30.0, "ETH": 25.0, "AAPL": 25.0, "GOLD": 20.0}
    asset_classes = {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", "AAPL": "equities", "GOLD": "commodities"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    rules = [v.rule for v in violations]
    assert "MIN_LIQUIDITY" in rules


def test_too_few_asset_classes():
    allocations = {"BTC": 50.0, "ETH": 45.0, "USDC": 5.0}
    asset_classes = {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", "USDC": "stablecoins"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    rules = [v.rule for v in violations]
    assert "MIN_DIVERSIFICATION" in rules


def test_no_leverage():
    allocations = {"BTC": 105.0, "USDC": -5.0, "ETH": 0.0}
    asset_classes = {"BTC": "cryptocurrencies", "USDC": "stablecoins", "ETH": "cryptocurrencies"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    rules = [v.rule for v in violations]
    assert "NO_LEVERAGE" in rules
''')

write("backend/tests/integration/test_auth.py", '''\
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "test@allocensus.com",
        "password": "TestPass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "wallet_address" in data
    assert data["wallet_address"].startswith("0x")


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {"email": "dup@allocensus.com", "password": "TestPass123", "full_name": "Dup"}
    await client.post("/api/auth/register", json=payload)
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "login@allocensus.com", "password": "TestPass123", "full_name": "Login User"
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login@allocensus.com", "password": "TestPass123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={
        "email": "login@allocensus.com", "password": "WrongPass999"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
''')

print("✅ Migration and tests complete.")
