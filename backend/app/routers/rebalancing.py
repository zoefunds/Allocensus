from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.rebalancing import RebalancingProposal, ProposalStatus
from app.models.portfolio import Portfolio
from app.schemas.rebalancing import ProposalCreate, ProposalResponse, RationaleResponse
from app.schemas.rules import InvestmentRulesResponse
from app.services.rebalancing_service import create_proposal, process_rationale_result
from app.services.genlayer_service import genlayer_service
from app.services.audit_service import log_event
from app.models.audit import AuditEventType
from app.dependencies import CurrentUser, DB
from app.utils.constraints import get_investment_rules
from typing import List
import uuid

router = APIRouter()
STAKE_WEI = 10**18


class TxHashSubmit(BaseModel):
    tx_hash: str
    wallet_address: str
    block_number: int
    proposal_version: str


async def _get_owned_proposal(proposal_id: str, user, db, *, with_portfolio: bool = True):
    query = select(RebalancingProposal).where(RebalancingProposal.id == uuid.UUID(proposal_id))
    if with_portfolio:
        query = query.options(
            selectinload(RebalancingProposal.portfolio).selectinload(Portfolio.assets),
            selectinload(RebalancingProposal.portfolio).selectinload(Portfolio.investor_profile),
            selectinload(RebalancingProposal.rationale),
        )
    result = await db.execute(query)
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.submitted_by != user.id and proposal.portfolio.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.get("/rules", response_model=InvestmentRulesResponse)
async def rules():
    return get_investment_rules()


@router.post("", response_model=ProposalResponse, status_code=201)
async def create(req: ProposalCreate, user: CurrentUser, db: DB):
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
    return await _get_owned_proposal(proposal_id, user, db)


@router.get("/{proposal_id}/call-data")
async def get_call_data(proposal_id: str, user: CurrentUser, db: DB):
    """
    Build and return the Genlayer transaction call data for this proposal.
    The frontend uses this to construct and sign the transaction with the
    user's own wallet — the backend never sees or uses any private key.
    """
    proposal = await _get_owned_proposal(proposal_id, user, db)
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
        stake_context        = {
            "staked": True,
            "stake_tx_hash": "",
            "stake_amount": STAKE_WEI,
        },
    )

    return {
        "proposal_id":   str(proposal.id),
        "call_data":     call_data,
        "contract":      genlayer_service.contract_address,
        "instructions":  (
            "Sign and broadcast this transaction using your connected wallet. "
            "Then POST the resulting tx_hash to /api/rebalancing/{id}/confirm-tx"
        ),
        "rules": get_investment_rules(),
    }


@router.post("/{proposal_id}/confirm-tx")
async def confirm_tx(proposal_id: str, body: TxHashSubmit, user: CurrentUser, db: DB):
    """
    Called by the frontend after the user has signed and broadcast the
    Genlayer transaction. Records the tx_hash and marks the proposal as
    pending consensus.
    """
    proposal = await _get_owned_proposal(proposal_id, user, db)
    if proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Proposal is not in draft status")

    proposal.genlayer_tx_hash = body.tx_hash
    proposal.status           = ProposalStatus.PENDING_CONSENSUS
    proposal.tx_wallet_address = body.wallet_address
    proposal.tx_authenticated_user_id = user.id
    proposal.tx_block_number = body.block_number
    proposal.proposal_version = body.proposal_version
    proposal.stake_wei = STAKE_WEI
    proposal.stake_refund_claimed = False
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
    proposal = await _get_owned_proposal(proposal_id, user, db)
    if not proposal.genlayer_tx_hash:
        raise HTTPException(status_code=404, detail="Proposal or tx_hash not found")

    raw = await genlayer_service.read_rationale(proposal.genlayer_tx_hash, proposal_id)
    if not raw:
        return {"status": "pending_consensus", "message": "Validators still processing — check back shortly"}

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


@router.delete("/{proposal_id}", status_code=204)
async def delete_proposal(proposal_id: str, user: CurrentUser, db: DB):
    proposal = await _get_owned_proposal(proposal_id, user, db)
    if proposal.status not in (ProposalStatus.DRAFT, ProposalStatus.FAILED, ProposalStatus.PENDING_CONSENSUS):
        raise HTTPException(status_code=400, detail="Only DRAFT, PENDING, or FAILED proposals can be deleted")
    await db.delete(proposal)
    await db.commit()


@router.get("/{proposal_id}/rationale", response_model=RationaleResponse)
async def get_rationale(proposal_id: str, user: CurrentUser, db: DB):
    from app.models.rebalancing import RationaleResult
    proposal = await _get_owned_proposal(proposal_id, user, db)
    rationale = proposal.rationale
    if not rationale:
        raise HTTPException(status_code=404, detail="Rationale not yet available")
    return rationale


@router.get("/{proposal_id}/stake")
async def get_stake_info(proposal_id: str, user: CurrentUser, db: DB):
    proposal = await _get_owned_proposal(proposal_id, user, db)
    stake_wei = int(proposal.stake_wei or 0)
    return {
        "proposal_id": str(proposal.id),
        "wallet_address": proposal.tx_wallet_address or "",
        "contract_address": genlayer_service.contract_address,
        "stake_wei": stake_wei,
        "refund_wei": stake_wei // 2 if stake_wei else 0,
        "claimable": bool(proposal.genlayer_tx_hash and proposal.rationale and proposal.tx_wallet_address),
        "claimed": bool(proposal.stake_refund_claimed),
        "proposal_version": proposal.proposal_version,
    }
