from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.portfolio import Portfolio, PortfolioAsset, PortfolioSnapshot
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate
from app.utils.constraints import validate_portfolio_constraints
import uuid
from datetime import datetime, timezone


async def get_portfolio_or_404(portfolio_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Portfolio:
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.assets))
        .where(Portfolio.id == portfolio_id, Portfolio.owner_id == user_id, Portfolio.is_active == True)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return p


async def create_portfolio(req: PortfolioCreate, user_id: uuid.UUID, db: AsyncSession) -> Portfolio:
    portfolio = Portfolio(
        owner_id=user_id,
        name=req.name,
        description=req.description,
        currency=req.currency,
        investor_profile_id=req.investor_profile_id,
    )
    db.add(portfolio)
    await db.flush()

    total_value = 0.0
    for asset_in in req.assets:
        value = asset_in.quantity * asset_in.current_price_usd
        total_value += value
        asset = PortfolioAsset(
            portfolio_id=portfolio.id,
            **asset_in.model_dump(),
            current_value_usd=value,
        )
        db.add(asset)

    portfolio.total_value_usd = total_value
    await db.flush()

    snapshot = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        total_value_usd=total_value,
        allocations={a.symbol: a.target_weight_pct for a in portfolio.assets},
    )
    db.add(snapshot)
    return portfolio


async def recalculate_weights(portfolio: Portfolio) -> None:
    total = sum(a.current_value_usd for a in portfolio.assets)
    portfolio.total_value_usd = total
    for asset in portfolio.assets:
        asset.current_weight_pct = (asset.current_value_usd / total * 100) if total > 0 else 0.0


async def check_drift(portfolio: Portfolio) -> list[dict]:
    """Return list of assets whose current weight drifts >5% from target."""
    drifts = []
    for asset in portfolio.assets:
        drift = abs(asset.current_weight_pct - asset.target_weight_pct)
        if drift >= 5.0:
            drifts.append({
                "symbol": asset.symbol,
                "current": asset.current_weight_pct,
                "target": asset.target_weight_pct,
                "drift": drift,
            })
    return drifts
