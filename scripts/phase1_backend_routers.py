"""ALLOCENSUS — Backend Routers"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("backend/app/routers/auth.py", '''\
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
)
from app.services.auth_service import register_user, login_user
from app.utils.security import (
    verify_refresh_token, create_access_token, create_refresh_token,
    verify_password, hash_password, generate_secure_token,
)
from app.models.user import User
from app.models.audit import AuditEventType
from app.services.audit_service import log_event
from app.dependencies import CurrentUser, DB

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: DB):
    return await register_user(req, db)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: DB):
    result = await login_user(req, db)
    await log_event(
        db, AuditEventType.USER_LOGIN,
        user_id=None,
        ip_address=request.client.host if request.client else None,
        metadata={"email": req.email},
    )
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: DB):
    payload = verify_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id), "role": user.role.value}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
        user_id=str(user.id),
        role=user.role.value,
    )


@router.post("/verify-email")
async def verify_email(token: str, db: DB):
    result = await db.execute(select(User).where(User.email_verification_token == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user.is_email_verified = True
    user.email_verification_token = None
    return {"message": "Email verified successfully"}


@router.post("/change-password")
async def change_password(req: PasswordChangeRequest, user: CurrentUser, db: DB):
    if not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = hash_password(req.new_password)
    await log_event(db, AuditEventType.PASSWORD_CHANGE, user_id=user.id)
    return {"message": "Password updated"}
''')

write("backend/app/routers/users.py", '''\
from fastapi import APIRouter
from sqlalchemy import select
from app.models.wallet import Wallet
from app.schemas.user import UserResponse, UserUpdate, WalletResponse, ExportKeyRequest
from app.services.wallet_service import export_private_key
from app.utils.security import verify_password
from app.dependencies import CurrentUser, DB
from fastapi import HTTPException
from app.models.audit import AuditEventType
from app.services.audit_service import log_event

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser, db: DB):
    wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = wallet_result.scalar_one_or_none()
    response = UserResponse.model_validate(user)
    response.wallet_address = wallet.address if wallet else None
    return response


@router.patch("/me", response_model=UserResponse)
async def update_me(req: UserUpdate, user: CurrentUser, db: DB):
    if req.full_name:
        user.full_name = req.full_name
    if req.email:
        user.email = req.email
        user.is_email_verified = False
    return UserResponse.model_validate(user)


@router.get("/me/wallet", response_model=WalletResponse)
async def get_wallet(user: CurrentUser, db: DB):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Wallet).options(selectinload(Wallet.keystore)).where(Wallet.user_id == user.id)
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return WalletResponse(address=wallet.address, chain_id=wallet.chain_id, derivation_path=wallet.derivation_path)


@router.post("/me/wallet/export-key")
async def export_key(req: ExportKeyRequest, user: CurrentUser, db: DB):
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=403, detail="Invalid password")
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Wallet).options(selectinload(Wallet.keystore)).where(Wallet.user_id == user.id)
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    pk = await export_private_key(wallet, req.password, user.hashed_password)
    await log_event(db, AuditEventType.KEY_EXPORT, user_id=user.id)
    return {"private_key": pk, "address": wallet.address}
''')

write("backend/app/routers/portfolios.py", '''\
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.portfolio import Portfolio, InvestorProfile
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    InvestorProfileCreate, InvestorProfileResponse,
)
from app.services.portfolio_service import create_portfolio, get_portfolio_or_404, recalculate_weights, check_drift
from app.services.audit_service import log_event
from app.models.audit import AuditEventType
from app.dependencies import CurrentUser, DB
from typing import List

router = APIRouter()


@router.get("", response_model=List[PortfolioResponse])
async def list_portfolios(user: CurrentUser, db: DB):
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.assets))
        .where(Portfolio.owner_id == user.id, Portfolio.is_active == True)
    )
    return result.scalars().all()


@router.post("", response_model=PortfolioResponse, status_code=201)
async def create(req: PortfolioCreate, user: CurrentUser, db: DB):
    portfolio = await create_portfolio(req, user.id, db)
    await log_event(db, AuditEventType.PORTFOLIO_CREATE, user_id=user.id, resource_id=str(portfolio.id))
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get(portfolio_id, user: CurrentUser, db: DB):
    import uuid
    return await get_portfolio_or_404(uuid.UUID(portfolio_id), user.id, db)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
async def update(portfolio_id, req: PortfolioUpdate, user: CurrentUser, db: DB):
    import uuid
    portfolio = await get_portfolio_or_404(uuid.UUID(portfolio_id), user.id, db)
    if req.name:
        portfolio.name = req.name
    if req.description is not None:
        portfolio.description = req.description
    await log_event(db, AuditEventType.PORTFOLIO_UPDATE, user_id=user.id, resource_id=portfolio_id)
    return portfolio


@router.delete("/{portfolio_id}", status_code=204)
async def delete(portfolio_id, user: CurrentUser, db: DB):
    import uuid
    portfolio = await get_portfolio_or_404(uuid.UUID(portfolio_id), user.id, db)
    portfolio.is_active = False
    await log_event(db, AuditEventType.PORTFOLIO_DELETE, user_id=user.id, resource_id=portfolio_id)


@router.get("/{portfolio_id}/drift")
async def get_drift(portfolio_id, user: CurrentUser, db: DB):
    import uuid
    portfolio = await get_portfolio_or_404(uuid.UUID(portfolio_id), user.id, db)
    drifts = await check_drift(portfolio)
    return {"portfolio_id": portfolio_id, "drifts": drifts, "rebalancing_recommended": len(drifts) > 0}


@router.post("/investor-profile", response_model=InvestorProfileResponse, status_code=201)
async def create_investor_profile(req: InvestorProfileCreate, user: CurrentUser, db: DB):
    profile = InvestorProfile(user_id=user.id, **req.model_dump())
    db.add(profile)
    await db.flush()
    return profile


@router.get("/investor-profile/me", response_model=List[InvestorProfileResponse])
async def get_investor_profiles(user: CurrentUser, db: DB):
    result = await db.execute(
        select(InvestorProfile).where(InvestorProfile.user_id == user.id)
    )
    return result.scalars().all()
''')

write("backend/app/routers/rebalancing.py", '''\
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.rebalancing import RebalancingProposal, ProposalStatus
from app.models.portfolio import Portfolio, InvestorProfile
from app.models.wallet import Wallet
from app.schemas.rebalancing import ProposalCreate, ProposalResponse, RationaleResponse
from app.services.rebalancing_service import create_proposal, submit_to_genlayer, process_rationale_result
from app.services.genlayer_service import genlayer_service
from app.services.wallet_service import get_signer_account
from app.services.audit_service import log_event
from app.models.audit import AuditEventType
from app.dependencies import CurrentUser, PMUser, DB
from typing import List
import uuid

router = APIRouter()


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


@router.post("/{proposal_id}/submit")
async def submit_proposal(proposal_id: str, user: PMUser, db: DB):
    """Submit draft proposal to Genlayer for AI evaluation."""
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

    wallet_result = await db.execute(
        select(Wallet).options(selectinload(Wallet.keystore)).where(Wallet.user_id == user.id)
    )
    wallet = wallet_result.scalar_one_or_none()
    if not wallet or not wallet.keystore:
        raise HTTPException(status_code=400, detail="Wallet not found")

    from app.utils.security import decrypt_private_key
    pk = decrypt_private_key(wallet.keystore.encrypted_private_key, user.hashed_password)

    profile = proposal.portfolio.investor_profile
    investor_profile_dict = {}
    if profile:
        investor_profile_dict = {
            "risk_tolerance": profile.risk_tolerance.value,
            "investment_horizon": profile.investment_horizon.value,
            "investment_objectives": profile.investment_objectives,
            "liquidity_requirements": profile.liquidity_requirements,
        }

    proposal = await submit_to_genlayer(proposal, investor_profile_dict, pk, user.email, db)
    await log_event(db, AuditEventType.PROPOSAL_SUBMIT, user_id=user.id, resource_id=proposal_id)
    return {"status": proposal.status.value, "tx_hash": proposal.genlayer_tx_hash}


@router.post("/{proposal_id}/poll-result")
async def poll_result(proposal_id: str, user: CurrentUser, db: DB):
    """Poll Genlayer for transaction result and persist rationale."""
    result = await db.execute(
        select(RebalancingProposal).where(RebalancingProposal.id == uuid.UUID(proposal_id))
    )
    proposal = result.scalar_one_or_none()
    if not proposal or not proposal.genlayer_tx_hash:
        raise HTTPException(status_code=404, detail="Proposal or tx_hash not found")

    raw = await genlayer_service.read_rationale(proposal.genlayer_tx_hash)
    if not raw:
        return {"status": "pending", "message": "Validators still processing"}

    rationale = await process_rationale_result(proposal, raw, user.email, db)
    event_type = AuditEventType.PROPOSAL_APPROVED if rationale.approved else AuditEventType.PROPOSAL_REJECTED
    await log_event(db, event_type, user_id=user.id, resource_id=proposal_id, on_chain_ref=proposal.genlayer_tx_hash)
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
''')

write("backend/app/routers/audit.py", '''\
from fastapi import APIRouter, Query
from sqlalchemy import select
from app.models.audit import AuditEvent, ComplianceLog
from app.dependencies import CurrentUser, DB
from datetime import datetime
from typing import Optional, List

router = APIRouter()


@router.get("/events")
async def get_audit_events(
    user: CurrentUser,
    db: DB,
    limit: int = Query(50, le=200),
    offset: int = 0,
    event_type: Optional[str] = None,
):
    query = select(AuditEvent).where(AuditEvent.user_id == user.id).order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
    if event_type:
        from app.models.audit import AuditEventType
        query = query.where(AuditEvent.event_type == event_type)
    result = await db.execute(query)
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type.value,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "ip_address": e.ip_address,
            "on_chain_ref": e.on_chain_ref,
            "metadata": e.metadata,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/compliance")
async def get_compliance_logs(user: CurrentUser, db: DB, limit: int = 50):
    result = await db.execute(
        select(ComplianceLog).order_by(ComplianceLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [{"id": str(l.id), "check_type": l.check_type, "passed": l.passed, "details": l.details, "created_at": l.created_at.isoformat()} for l in logs]
''')

write("backend/app/routers/admin.py", '''\
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from app.models.user import User, UserRole
from app.models.portfolio import Portfolio
from app.models.rebalancing import RebalancingProposal
from app.dependencies import AdminUser, DB
from app.models.audit import AuditEventType
from app.services.audit_service import log_event

router = APIRouter()


@router.get("/stats")
async def get_stats(admin: AdminUser, db: DB):
    users_count = await db.scalar(select(func.count()).select_from(User))
    portfolios_count = await db.scalar(select(func.count()).select_from(Portfolio))
    proposals_count = await db.scalar(select(func.count()).select_from(RebalancingProposal))
    return {
        "total_users": users_count,
        "total_portfolios": portfolios_count,
        "total_proposals": proposals_count,
    }


@router.get("/users")
async def list_users(admin: AdminUser, db: DB, limit: int = 50, offset: int = 0):
    result = await db.execute(select(User).limit(limit).offset(offset).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [{"id": str(u.id), "email": u.email, "full_name": u.full_name, "role": u.role.value, "is_active": u.is_active, "created_at": u.created_at.isoformat()} for u in users]


@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, admin: AdminUser, db: DB):
    try:
        new_role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    await log_event(db, AuditEventType.ADMIN_ACTION, user_id=admin.id, resource_id=user_id, metadata={"action": "role_change", "new_role": role})
    return {"message": f"Role updated to {role}"}


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, admin: AdminUser, db: DB):
    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await log_event(db, AuditEventType.ADMIN_ACTION, user_id=admin.id, resource_id=user_id, metadata={"action": "deactivate"})
    return {"message": "User deactivated"}
''')

write("backend/app/workers/__init__.py", "")

write("backend/app/workers/celery_app.py", '''\
from celery import Celery
from app.config import settings

celery_app = Celery(
    "allocensus",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
''')

write("backend/app/workers/tasks.py", '''\
from app.workers.celery_app import celery_app
import asyncio
import structlog

log = structlog.get_logger()


@celery_app.task(bind=True, max_retries=10, default_retry_delay=10)
def poll_genlayer_result(self, proposal_id: str, tx_hash: str, user_email: str):
    """Background task: poll Genlayer until tx is confirmed, then save rationale."""
    from app.services.genlayer_service import genlayer_service
    from app.database import AsyncSessionLocal
    from app.models.rebalancing import RebalancingProposal, ProposalStatus
    from app.services.rebalancing_service import process_rationale_result
    from sqlalchemy import select
    import uuid

    async def _run():
        raw = await genlayer_service.read_rationale(tx_hash)
        if not raw:
            raise Exception("Result not ready")
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RebalancingProposal).where(RebalancingProposal.id == uuid.UUID(proposal_id))
            )
            proposal = result.scalar_one_or_none()
            if proposal and proposal.status == ProposalStatus.PENDING_CONSENSUS:
                await process_rationale_result(proposal, raw, user_email, db)
                await db.commit()
                log.info("rationale_saved", proposal_id=proposal_id)

    try:
        asyncio.run(_run())
    except Exception as exc:
        log.warning("poll_retry", proposal_id=proposal_id, attempt=self.request.retries)
        raise self.retry(exc=exc)
''')

print("✅ Routers and workers complete.")
