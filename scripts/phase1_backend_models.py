"""
ALLOCENSUS — Phase 1 Backend Models
Creates: all SQLAlchemy models (user, wallet, portfolio, rebalancing, audit)
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("backend/app/models/__init__.py", """\
from app.models.user import User, UserRole
from app.models.wallet import Wallet, EncryptedKeystore
from app.models.portfolio import Portfolio, PortfolioAsset, PortfolioSnapshot, InvestorProfile
from app.models.rebalancing import RebalancingProposal, RationaleResult, ValidatorResponse, ProposalStatus
from app.models.audit import AuditEvent, ComplianceLog, ReportExport

__all__ = [
    "User", "UserRole",
    "Wallet", "EncryptedKeystore",
    "Portfolio", "PortfolioAsset", "PortfolioSnapshot", "InvestorProfile",
    "RebalancingProposal", "RationaleResult", "ValidatorResponse", "ProposalStatus",
    "AuditEvent", "ComplianceLog", "ReportExport",
]
""")

write("backend/app/models/user.py", '''\
import uuid
import enum
from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PORTFOLIO_MANAGER = "portfolio_manager"
    ANALYST = "analyst"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.ANALYST)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[str | None] = mapped_column(nullable=True)

    wallet: Mapped["Wallet | None"] = relationship("Wallet", back_populates="user", uselist=False)
    portfolios: Mapped[list["Portfolio"]] = relationship("Portfolio", back_populates="owner")
    audit_events: Mapped[list["AuditEvent"]] = relationship("AuditEvent", back_populates="user")
''')

write("backend/app/models/wallet.py", '''\
import uuid
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base, TimestampMixin


class Wallet(Base, TimestampMixin):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(42), unique=True, nullable=False, index=True)
    derivation_path: Mapped[str] = mapped_column(String(64), nullable=False, default="m/44'/60'/0'/0/0")
    chain_id: Mapped[int] = mapped_column(nullable=False, default=61999)  # StudioNet chain ID

    user: Mapped["User"] = relationship("User", back_populates="wallet")
    keystore: Mapped["EncryptedKeystore | None"] = relationship("EncryptedKeystore", back_populates="wallet", uselist=False)


class EncryptedKeystore(Base, TimestampMixin):
    __tablename__ = "encrypted_keystores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), unique=True, nullable=False)
    encrypted_private_key: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_mnemonic: Mapped[str | None] = mapped_column(Text, nullable=True)

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="keystore")
''')

write("backend/app/models/portfolio.py", '''\
import uuid
import enum
from sqlalchemy import String, ForeignKey, Text, Float, Integer, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base, TimestampMixin


class RiskTolerance(str, enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


class InvestmentHorizon(str, enum.Enum):
    SHORT = "short"       # < 1 year
    MEDIUM = "medium"     # 1-5 years
    LONG = "long"         # 5-10 years
    VERY_LONG = "very_long"  # > 10 years


class InvestorProfile(Base, TimestampMixin):
    __tablename__ = "investor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    risk_tolerance: Mapped[RiskTolerance] = mapped_column(SAEnum(RiskTolerance), nullable=False)
    investment_horizon: Mapped[InvestmentHorizon] = mapped_column(SAEnum(InvestmentHorizon), nullable=False)
    investment_objectives: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    liquidity_requirements: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    portfolios: Mapped[list["Portfolio"]] = relationship("Portfolio", back_populates="investor_profile")


class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    investor_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("investor_profiles.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_value_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    last_rebalanced_at: Mapped[str | None] = mapped_column(nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="portfolios")
    investor_profile: Mapped["InvestorProfile | None"] = relationship("InvestorProfile", back_populates="portfolios")
    assets: Mapped[list["PortfolioAsset"]] = relationship("PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots: Mapped[list["PortfolioSnapshot"]] = relationship("PortfolioSnapshot", back_populates="portfolio")
    proposals: Mapped[list["RebalancingProposal"]] = relationship("RebalancingProposal", back_populates="portfolio")


class PortfolioAsset(Base, TimestampMixin):
    __tablename__ = "portfolio_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    current_price_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_value_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_weight_pct: Mapped[float] = mapped_column(Float, nullable=False)
    current_weight_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    coingecko_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    contract_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    chain: Mapped[str | None] = mapped_column(String(32), nullable=True)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="assets")


class PortfolioSnapshot(Base, TimestampMixin):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    total_value_usd: Mapped[float] = mapped_column(Float, nullable=False)
    allocations: Mapped[dict] = mapped_column(JSON, nullable=False)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="snapshots")
''')

write("backend/app/models/rebalancing.py", '''\
import uuid
import enum
from sqlalchemy import String, ForeignKey, Text, Float, JSON, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base, TimestampMixin


class ProposalStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_CONSENSUS = "pending_consensus"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class RebalancingProposal(Base, TimestampMixin):
    __tablename__ = "rebalancing_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[ProposalStatus] = mapped_column(SAEnum(ProposalStatus), nullable=False, default=ProposalStatus.DRAFT)

    current_allocations: Mapped[dict] = mapped_column(JSON, nullable=False)
    proposed_allocations: Mapped[dict] = mapped_column(JSON, nullable=False)
    market_context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    genlayer_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    genlayer_tx_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    constraint_violations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="proposals")
    rationale: Mapped["RationaleResult | None"] = relationship("RationaleResult", back_populates="proposal", uselist=False)
    validator_responses: Mapped[list["ValidatorResponse"]] = relationship("ValidatorResponse", back_populates="proposal")


class RationaleResult(Base, TimestampMixin):
    __tablename__ = "rationale_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rebalancing_proposals.id", ondelete="CASCADE"), unique=True, nullable=False)

    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)

    rationale_text: Mapped[str] = mapped_column(Text, nullable=False)
    risk_analysis: Mapped[str] = mapped_column(Text, nullable=True)
    constraint_analysis: Mapped[str] = mapped_column(Text, nullable=True)
    diversification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity_assessment: Mapped[str] = mapped_column(Text, nullable=True)
    objective_alignment: Mapped[str] = mapped_column(Text, nullable=True)

    validator_consensus: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    raw_contract_output: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    proposal: Mapped["RebalancingProposal"] = relationship("RebalancingProposal", back_populates="rationale")


class ValidatorResponse(Base, TimestampMixin):
    __tablename__ = "validator_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rebalancing_proposals.id", ondelete="CASCADE"), nullable=False)
    validator_address: Mapped[str] = mapped_column(String(64), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=True)
    raw_output: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    proposal: Mapped["RebalancingProposal"] = relationship("RebalancingProposal", back_populates="validator_responses")
''')

write("backend/app/models/audit.py", '''\
import uuid
import enum
from sqlalchemy import String, ForeignKey, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base, TimestampMixin


class AuditEventType(str, enum.Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    PASSWORD_CHANGE = "password_change"
    KEY_EXPORT = "key_export"
    PORTFOLIO_CREATE = "portfolio_create"
    PORTFOLIO_UPDATE = "portfolio_update"
    PORTFOLIO_DELETE = "portfolio_delete"
    PROPOSAL_SUBMIT = "proposal_submit"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_REJECTED = "proposal_rejected"
    REPORT_EXPORT = "report_export"
    ADMIN_ACTION = "admin_action"


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[AuditEventType] = mapped_column(SAEnum(AuditEventType), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    on_chain_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)

    user: Mapped["User | None"] = relationship("User", back_populates="audit_events")


class ComplianceLog(Base, TimestampMixin):
    __tablename__ = "compliance_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    proposal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    check_type: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class ReportExport(Base, TimestampMixin):
    __tablename__ = "report_exports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    portfolio_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
''')

print("✅ Models complete.")
