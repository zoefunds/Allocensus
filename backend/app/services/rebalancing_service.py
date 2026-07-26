import json
import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError, field_validator
from app.models.rebalancing import RebalancingProposal, RationaleResult, ProposalStatus
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.rebalancing import ProposalCreate
from app.utils.constraints import validate_portfolio_constraints
from app.services.genlayer_service import genlayer_service
from app.services.notification_service import send_rationale_ready_email
from app.services.price_service import get_market_context

log = structlog.get_logger()


class ContractRationalePayload(BaseModel):
    approved: bool
    confidence_score: float
    overall_rationale: str
    constraint_analysis: str
    risk_analysis: str
    diversification_score: int
    diversification_analysis: str
    liquidity_assessment: str
    objective_alignment: str
    market_context_analysis: str
    key_risks_introduced: list[str]
    key_risks_mitigated: list[str]
    recommendation: str

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.5 <= v <= 1.0):
            raise ValueError("confidence_score must be between 0.5 and 1.0")
        return v

    @field_validator("diversification_score")
    @classmethod
    def validate_diversification(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("diversification_score must be between 0 and 100")
        return v


async def create_proposal(req: ProposalCreate, user: User, db: AsyncSession) -> RebalancingProposal:
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.assets))
        .where(Portfolio.id == req.portfolio_id, Portfolio.owner_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    current_allocs = {a.symbol: a.current_weight_pct for a in portfolio.assets}
    # Allow caller to supply current allocations when portfolio has no assets yet
    if not current_allocs and req.current_allocations:
        current_allocs = req.current_allocations
    asset_classes = {a.symbol: a.asset_class for a in portfolio.assets}
    violations     = validate_portfolio_constraints(req.proposed_allocations, asset_classes)
    market_ctx     = await get_market_context()
    if req.market_context:
        market_ctx.update(req.market_context.model_dump(exclude_none=True))

    proposal = RebalancingProposal(
        portfolio_id          = req.portfolio_id,
        submitted_by          = user.id,
        current_allocations   = current_allocs,
        proposed_allocations  = req.proposed_allocations,
        market_context        = market_ctx,
        constraint_violations = [v.__dict__ for v in violations],
        notes                 = req.notes,
        status                = ProposalStatus.DRAFT,
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    return proposal


async def process_rationale_result(
    proposal: RebalancingProposal,
    raw_result: dict | str,
    user_email: str,
    db: AsyncSession,
) -> RationaleResult:
    # Unwrap RPC envelope
    if isinstance(raw_result, dict):
        data = raw_result.get("result") or raw_result.get("output") or raw_result
    else:
        data = raw_result

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Malformed contract output") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Malformed contract output")

    try:
        payload = ContractRationalePayload.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail="Malformed contract output") from exc

    approved = payload.approved

    rationale = RationaleResult(
        proposal_id           = proposal.id,
        approved              = approved,
        confidence_score      = payload.confidence_score,
        rationale_text        = payload.overall_rationale,
        risk_analysis         = payload.risk_analysis,
        constraint_analysis   = payload.constraint_analysis,
        diversification_score = payload.diversification_score,
        liquidity_assessment  = payload.liquidity_assessment,
        objective_alignment   = payload.objective_alignment,
        validator_consensus   = {
            "market_context_analysis": payload.market_context_analysis,
            "key_risks_introduced":    payload.key_risks_introduced,
            "key_risks_mitigated":     payload.key_risks_mitigated,
            "recommendation":          payload.recommendation,
        },
        raw_contract_output   = data,
    )
    db.add(rationale)
    proposal.status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
    proposal.tx_timestamp = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(rationale)
    await send_rationale_ready_email(user_email, str(proposal.id), approved)
    log.info("rationale_persisted", proposal_id=str(proposal.id), approved=approved)
    return rationale
