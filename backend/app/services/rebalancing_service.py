import json
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.rebalancing import RebalancingProposal, RationaleResult, ProposalStatus
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.rebalancing import ProposalCreate
from app.utils.constraints import validate_portfolio_constraints
from app.services.genlayer_service import genlayer_service
from app.services.notification_service import send_rationale_ready_email
from app.services.price_service import get_market_context

log = structlog.get_logger()


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
    asset_classes  = {a.symbol: a.asset_class for a in portfolio.assets}
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
        except json.JSONDecodeError:
            data = {}

    if not isinstance(data, dict):
        data = {}

    approved = bool(data.get("approved", False))

    rationale = RationaleResult(
        proposal_id           = proposal.id,
        approved              = approved,
        confidence_score      = data.get("confidence_score"),
        rationale_text        = data.get("overall_rationale") or data.get("rationale_text", ""),
        risk_analysis         = data.get("risk_analysis"),
        constraint_analysis   = data.get("constraint_analysis"),
        diversification_score = data.get("diversification_score"),
        liquidity_assessment  = data.get("liquidity_assessment"),
        objective_alignment   = data.get("objective_alignment"),
        validator_consensus   = {
            "market_context_analysis": data.get("market_context_analysis"),
            "key_risks_introduced":    data.get("key_risks_introduced", []),
            "key_risks_mitigated":     data.get("key_risks_mitigated", []),
            "recommendation":          data.get("recommendation"),
            "hard_constraint_fail":    data.get("hard_constraint_fail", False),
            "violations_count":        data.get("violations_count", 0),
            "analytics":               data.get("analytics", {}),
        },
        raw_contract_output   = data,
    )
    db.add(rationale)
    proposal.status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
    await db.commit()
    await db.refresh(rationale)
    await send_rationale_ready_email(user_email, str(proposal.id), approved)
    log.info("rationale_persisted", proposal_id=str(proposal.id), approved=approved)
    return rationale
