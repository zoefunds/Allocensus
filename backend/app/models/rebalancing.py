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
