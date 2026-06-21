import uuid
import enum
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, Float, Integer, JSON, Enum as SAEnum, DateTime
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
    risk_tolerance: Mapped[RiskTolerance] = mapped_column(SAEnum(RiskTolerance, values_callable=lambda x: [e.value for e in x]), nullable=False)
    investment_horizon: Mapped[InvestmentHorizon] = mapped_column(SAEnum(InvestmentHorizon, values_callable=lambda x: [e.value for e in x]), nullable=False)
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
    last_rebalanced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
