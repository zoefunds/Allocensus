from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.rebalancing import RebalancingProposal, ProposalStatus
from app.models.portfolio import Portfolio
from app.schemas.rebalancing import ProposalCreate, ProposalResponse, RationaleResponse
from app.services.rebalancing_service import create_proposal, process_rationale_result
from app.services.genlayer_service import genlayer_service
from app.services.audit_service import log_event
from app.models.audit import AuditEventType
from app.dependencies import CurrentUser, PMUser, DB
from typing import List
import uuid

router = APIRouter()


class TxHashSubmit(BaseModel):
    tx_hash: str


@router.post("", response_model=ProposalResponse, status_code=201)
async def create(req: ProposalCreate, user: PMUser, db: DB):
    proposal = await create_proposal(req, user, db)
    return proposal


@router.get("", response_model=List[ProposalResponse])
async def list_proposals(user: CurrentUser, db: DB):
    result = await db.execute(
        select(RebalancingProposal)
        .join(Portfolio)
        .where(Portfolio.owner_id == user.id)
        .order_by(RebalancingProposal.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(proposal_id: str, user: CurrentUser, db: DB):
    result = await db.execute(
        select(RebalancingProposal)
        .options(selectinload(RebalancingProposal.rationale))
        .where(RebalancingProposal.id == uuid.UUID(proposal_id))
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.get("/{proposal_id}/call-data")
async def get_call_data(proposal_id: str, user: PMUser, db: DB):
    """
    Build and return the Genlayer transaction call data for this proposal.
    The frontend uses this to construct and sign the transaction with the
    user's own wallet — the backend never sees or uses any private key.
    """
    result = await db.execute(
        select(RebalancingProposal)
        .options(
            selectinload(RebalancingProposal.portfolio).selectinload(Portfolio.assets),
            selectinload(RebalancingProposal.portfolio).selectinload(Portfolio.investor_profile),
        )
        .where(RebalancingProposal.id == uuid.UUID(proposal_id))
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft proposals can be submitted")

    portfolio = proposal.portfolio
    profile   = portfolio.investor_profile

    # Build asset_classes map from portfolio assets
    asset_classes = {
        asset.symbol: asset.asset_class
        for asset in portfolio.assets
    }

    investor_profile_dict = {}
    if profile:
        investor_profile_dict = {
            "risk_tolerance":         profile.risk_tolerance.value,
            "investment_horizon":     profile.investment_horizon.value,
            "investment_objectives":  profile.investment_objectives or ["capital growth"],
            "liquidity_requirements": profile.liquidity_requirements or "standard",
        }

    market_context = proposal.market_context or {}

    call_data = genlayer_service.build_call_data(
        proposal_id          = str(proposal.id),
        current_allocations  = proposal.current_allocations or {},
        proposed_allocations = proposal.proposed_allocations or {},
        asset_classes        = asset_classes,
        investor_profile     = investor_profile_dict,
        market_context       = market_context,
    )

    return {
        "proposal_id":   str(proposal.id),
        "call_data":     call_data,
        "contract":      genlayer_service.contract_address,
        "instructions":  (
            "Sign and broadcast this transaction using your connected wallet. "
            "Then POST the resulting tx_hash to /api/rebalancing/{id}/confirm-tx"
        ),
    }


@router.post("/{proposal_id}/confirm-tx")
async def confirm_tx(proposal_id: str, body: TxHashSubmit, user: PMUser, db: DB):
    """
    Called by the frontend after the user has signed and broadcast the
    Genlayer transaction. Records the tx_hash and marks the proposal as
    pending consensus.
    """
    result = await db.execute(
        select(RebalancingProposal)
        .where(RebalancingProposal.id == uuid.UUID(proposal_id))
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Proposal is not in draft status")

    proposal.genlayer_tx_hash = body.tx_hash
    proposal.status           = ProposalStatus.PENDING_CONSENSUS
    await db.commit()

    await log_event(
        db,
        AuditEventType.PROPOSAL_SUBMIT,
        user_id     = user.id,
        resource_id = proposal_id,
        on_chain_ref = body.tx_hash,
    )

    return {"status": proposal.status.value, "tx_hash": body.tx_hash}


@router.post("/{proposal_id}/poll-result")
async def poll_result(proposal_id: str, user: CurrentUser, db: DB):
    """Poll Genlayer for transaction result and persist rationale once consensus is reached."""
    result = await db.execute(
        select(RebalancingProposal).where(RebalancingProposal.id == uuid.UUID(proposal_id))
    )
    proposal = result.scalar_one_or_none()
    if not proposal or not proposal.genlayer_tx_hash:
        raise HTTPException(status_code=404, detail="Proposal or tx_hash not found")

    raw = await genlayer_service.read_rationale(proposal.genlayer_tx_hash)
    if not raw:
        return {"status": "pending", "message": "Validators still processing — check back shortly"}

    rationale  = await process_rationale_result(proposal, raw, user.email, db)
    event_type = (
        AuditEventType.PROPOSAL_APPROVED
        if rationale.approved
        else AuditEventType.PROPOSAL_REJECTED
    )
    await log_event(
        db,
        event_type,
        user_id      = user.id,
        resource_id  = proposal_id,
        on_chain_ref = proposal.genlayer_tx_hash,
    )
    return {"status": proposal.status.value, "approved": rationale.approved}


@router.get("/{proposal_id}/rationale", response_model=RationaleResponse)
async def get_rationale(proposal_id: str, user: CurrentUser, db: DB):
    from app.models.rebalancing import RationaleResult
    result = await db.execute(
        select(RationaleResult).where(RationaleResult.proposal_id == uuid.UUID(proposal_id))
    )
    rationale = result.scalar_one_or_none()
    if not rationale:
        raise HTTPException(status_code=404, detail="Rationale not yet available")
    return rationale
