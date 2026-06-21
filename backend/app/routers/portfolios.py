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
