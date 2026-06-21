"""ALLOCENSUS — Pydantic schemas"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("backend/app/schemas/__init__.py", "")

write("backend/app/schemas/auth.py", '''\
from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a number")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    wallet_address: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
''')

write("backend/app/schemas/user.py", '''\
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    wallet_address: str | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None


class WalletResponse(BaseModel):
    address: str
    chain_id: int
    derivation_path: str


class ExportKeyRequest(BaseModel):
    password: str
''')

write("backend/app/schemas/portfolio.py", '''\
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
''')

write("backend/app/schemas/rebalancing.py", '''\
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


class AllocationItem(BaseModel):
    symbol: str
    current_weight_pct: float
    proposed_weight_pct: float
    asset_class: str


class MarketContext(BaseModel):
    volatility_indicator: Optional[str] = None
    macro_signals: Optional[str] = None
    market_regime: Optional[str] = None
    additional_context: Optional[str] = None


class ProposalCreate(BaseModel):
    portfolio_id: uuid.UUID
    proposed_allocations: Dict[str, float]
    market_context: MarketContext = MarketContext()
    notes: Optional[str] = None


class ConstraintViolationOut(BaseModel):
    rule: str
    message: str
    current_value: float
    limit: float


class ProposalResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    status: str
    current_allocations: Dict[str, Any]
    proposed_allocations: Dict[str, Any]
    constraint_violations: List[ConstraintViolationOut]
    genlayer_tx_hash: Optional[str]
    notes: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class RationaleResponse(BaseModel):
    id: uuid.UUID
    proposal_id: uuid.UUID
    approved: bool
    confidence_score: Optional[float]
    rationale_text: str
    risk_analysis: Optional[str]
    constraint_analysis: Optional[str]
    diversification_score: Optional[float]
    liquidity_assessment: Optional[str]
    objective_alignment: Optional[str]
    validator_consensus: Dict[str, Any]
    created_at: datetime
    model_config = {"from_attributes": True}
''')

print("✅ Schemas complete.")
