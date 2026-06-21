from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
import uuid


class AssetIn(BaseModel):
    symbol: str
    name: str
    asset_class: str
    quantity: float
    current_price_usd: float
    target_weight_pct: float
    coingecko_id: Optional[str] = None
    contract_address: Optional[str] = None
    chain: Optional[str] = None

    @field_validator("asset_class")
    @classmethod
    def validate_asset_class(cls, v: str) -> str:
        valid = {"cryptocurrencies", "tokenised_rwa", "defi_protocols", "equities",
                 "fixed_income", "commodities", "stablecoins", "cash"}
        if v not in valid:
            raise ValueError(f"asset_class must be one of {valid}")
        return v


class AssetResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    asset_class: str
    quantity: float
    current_price_usd: float
    current_value_usd: float
    target_weight_pct: float
    current_weight_pct: float
    model_config = {"from_attributes": True}


class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    currency: str = "USD"
    aum: Optional[float] = None
    investor_profile: Optional[str] = None      # e.g. "balanced"
    allowed_asset_classes: Optional[List[str]] = None
    investor_profile_id: Optional[uuid.UUID] = None
    assets: List[AssetIn] = []


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    total_value_usd: float
    currency: str
    is_active: bool
    created_at: datetime
    assets: List[AssetResponse] = []
    model_config = {"from_attributes": True}


class InvestorProfileCreate(BaseModel):
    risk_tolerance: str
    investment_horizon: str
    investment_objectives: List[str]
    liquidity_requirements: Optional[str] = None
    notes: Optional[str] = None


class InvestorProfileResponse(BaseModel):
    id: uuid.UUID
    risk_tolerance: str
    investment_horizon: str
    investment_objectives: List[str]
    model_config = {"from_attributes": True}
